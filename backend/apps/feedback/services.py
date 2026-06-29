import logging
from difflib import SequenceMatcher

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import DomainError
from apps.feedback.github_enrichment import build_issue_create_payload, enrich_created_issue
from apps.feedback.github_sync import GitHubSyncResult, IntegrationMessage, github_issue_create_hint, parse_github_error
from apps.feedback.models import (
    Feedback,
    FeedbackAnalysis,
    FeedbackCategory,
    FeedbackHistory,
    FeedbackModule,
    FeedbackPriority,
    FeedbackSeverity,
    FeedbackStatus,
    GitHubIssueMapping,
)

logger = logging.getLogger(__name__)

DUPLICATE_THRESHOLD = 0.72

CATEGORY_KEYWORDS = {
    FeedbackCategory.BUG: ["bug", "error", "broken", "crash", "not working", "failed", "500", "404"],
    FeedbackCategory.FEATURE: ["feature", "add", "wish", "would like", "request"],
    FeedbackCategory.PERFORMANCE: ["slow", "lag", "timeout", "performance", "loading"],
    FeedbackCategory.SECURITY: ["security", "unauthorized", "hack", "vulnerability", "password leak"],
    FeedbackCategory.UI_UX: ["ui", "ux", "layout", "design", "confusing", "button", "screen"],
    FeedbackCategory.CONTENT: ["typo", "content", "translation", "sanskrit", "tamil", "incorrect text"],
    FeedbackCategory.COMPLAINT: ["complaint", "unhappy", "frustrated", "terrible", "worst"],
    FeedbackCategory.APPRECIATION: ["thank", "great", "excellent", "love", "appreciation", "amazing"],
    FeedbackCategory.COURSE: ["course", "lesson", "syllabus", "curriculum"],
    FeedbackCategory.ACHARYA: ["acharya", "teacher", "faculty"],
}

MODULE_KEYWORDS = {
    FeedbackModule.ATTENDANCE: ["attendance", "present", "absent", "mark attendance"],
    FeedbackModule.ADMISSIONS: ["admission", "application", "apply", "document upload"],
    FeedbackModule.DONATIONS: ["donation", "razorpay", "receipt", "payment", "sponsor"],
    FeedbackModule.HOSTEL: ["hostel", "room", "warden", "mess"],
    FeedbackModule.LMS: ["lesson", "practice", "video", "audio", "learning", "chant"],
    FeedbackModule.COMMUNITY: ["forum", "event", "community", "rsvp"],
    FeedbackModule.CURRICULUM: ["curriculum", "syllabus", "module"],
}

SEVERITY_KEYWORDS = {
    FeedbackSeverity.CRITICAL: ["cannot login", "data loss", "security", "production down", "everyone"],
    FeedbackSeverity.HIGH: ["not saved", "blocked", "cannot", "failed", "urgent"],
    FeedbackSeverity.LOW: ["minor", "cosmetic", "suggestion", "nice to have"],
}

PRIORITY_MAP = {
    FeedbackSeverity.CRITICAL: FeedbackPriority.P1,
    FeedbackSeverity.HIGH: FeedbackPriority.P2,
    FeedbackSeverity.MEDIUM: FeedbackPriority.P3,
    FeedbackSeverity.LOW: FeedbackPriority.P4,
}

TEAM_MAP = {
    FeedbackModule.ATTENDANCE: "learning-team",
    FeedbackModule.LMS: "learning-team",
    FeedbackModule.CURRICULUM: "curriculum-team",
    FeedbackModule.ADMISSIONS: "admissions-team",
    FeedbackModule.DONATIONS: "finance-team",
    FeedbackModule.HOSTEL: "operations-team",
    FeedbackModule.COMMUNITY: "community-team",
    FeedbackModule.PLATFORM: "platform-team",
}


class FeedbackAnalysisService:
    @classmethod
    def analyze(cls, feedback: Feedback) -> FeedbackAnalysis:
        text = f"{feedback.title} {feedback.description}".lower()

        category = feedback.category
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                category = cat
                break

        source_module = feedback.source_module
        for mod, keywords in MODULE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                source_module = mod
                break

        severity = FeedbackSeverity.MEDIUM
        for sev, keywords in SEVERITY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                severity = sev
                break

        if category == FeedbackCategory.APPRECIATION:
            severity = FeedbackSeverity.LOW

        priority = PRIORITY_MAP.get(severity, FeedbackPriority.P3)
        sentiment = cls._sentiment(text, category)
        summary = cls._summary(feedback, category, source_module)
        root_cause = cls._root_cause(feedback, category, source_module)
        confidence = cls._confidence(text, category, source_module)
        team = TEAM_MAP.get(source_module, "platform-team")
        # App dev feedback is Super Admin only — route all non-appreciation items to GitHub.
        create_github = category != FeedbackCategory.APPRECIATION

        draft = cls._github_draft(feedback, category, source_module, severity, priority, summary, root_cause, confidence)
        raw = {
            "category": category,
            "severity": severity,
            "priority": priority,
            "module": source_module,
            "summary": summary,
            "root_cause": root_cause,
            "confidence": float(confidence),
            "create_github_issue": create_github,
        }

        analysis, _ = FeedbackAnalysis.objects.update_or_create(
            feedback=feedback,
            defaults={
                "sentiment": sentiment,
                "ai_category": category,
                "ai_summary": summary,
                "root_cause_suggestion": root_cause,
                "confidence": confidence,
                "recommended_priority": priority,
                "recommended_team": team,
                "create_github_issue": create_github,
                "github_issue_draft": draft,
                "raw_analysis": raw,
            },
        )
        return analysis

    @staticmethod
    def _sentiment(text: str, category: str) -> str:
        if category == FeedbackCategory.APPRECIATION:
            return "positive"
        if category == FeedbackCategory.COMPLAINT or any(w in text for w in ["angry", "frustrated", "terrible"]):
            return "negative"
        return "neutral"

    @staticmethod
    def _summary(feedback: Feedback, category: str, module: str) -> str:
        first_line = feedback.description.strip().split("\n")[0][:200]
        return f"{module.replace('_', ' ').title()} – {first_line}"

    @staticmethod
    def _root_cause(feedback: Feedback, category: str, module: str) -> str:
        text = feedback.description.lower()
        if "not saved" in text or "disappear" in text:
            return "Possible API validation failure or database transaction rollback."
        if "slow" in text or "timeout" in text:
            return "Possible performance bottleneck or missing database index."
        if category == FeedbackCategory.SECURITY:
            return "Review authentication, authorization, and input validation paths."
        if module == FeedbackModule.ATTENDANCE:
            return "Inspect attendance mark API and session/batch scoping."
        return "Requires developer investigation; check recent deployments and module logs."

    @staticmethod
    def _confidence(text: str, category: str, module: str) -> float:
        score = 0.65
        if any(kw in text for kw in CATEGORY_KEYWORDS.get(category, [])):
            score += 0.15
        if any(kw in text for kw in MODULE_KEYWORDS.get(module, [])):
            score += 0.1
        if len(text) > 80:
            score += 0.05
        return min(round(score, 2), 0.98)

    @classmethod
    def _github_draft(cls, feedback, category, module, severity, priority, summary, root_cause, confidence) -> str:
        reporter = feedback.reporter_type or ("Anonymous" if feedback.is_anonymous else "User")
        return (
            f"Title:\n{module} - {feedback.title}\n\n"
            f"Environment:\n{feedback.environment}\n\n"
            f"Application Version:\n{feedback.app_version or 'N/A'}\n\n"
            f"Module:\n{module}\n\n"
            f"Reporter:\n{reporter}\n\n"
            f"Severity:\n{severity}\n\n"
            f"Priority:\n{priority}\n\n"
            f"AI Summary:\n{summary}\n\n"
            f"Suggested Root Cause:\n{root_cause}\n\n"
            f"Steps to Reproduce:\n{feedback.steps_to_reproduce or feedback.description}\n\n"
            f"Expected Result:\n{feedback.expected_result or '—'}\n\n"
            f"Actual Result:\n{feedback.actual_result or '—'}\n\n"
            f"Confidence:\n{int(confidence * 100)}%\n\n"
            f"Feedback ID: {feedback.feedback_number}"
        )


class DuplicateDetectionService:
    @classmethod
    def find_duplicate(cls, feedback: Feedback) -> Feedback | None:
        candidates = Feedback.objects.filter(
            is_deleted=False,
            source_module=feedback.source_module,
            status__in=[
                FeedbackStatus.GITHUB_CREATED,
                FeedbackStatus.IN_PROGRESS,
                FeedbackStatus.AI_ANALYZED,
                FeedbackStatus.PENDING_APPROVAL,
            ],
        ).exclude(id=feedback.id).order_by("-created_at")[:50]

        text = f"{feedback.title} {feedback.description}".lower()
        for candidate in candidates:
            other = f"{candidate.title} {candidate.description}".lower()
            ratio = SequenceMatcher(None, text, other).ratio()
            if ratio >= DUPLICATE_THRESHOLD:
                return candidate
        return None


class GitHubIntegrationService:
    @classmethod
    def _github_cfg(cls) -> dict:
        return getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("github", {})

    @staticmethod
    def is_enabled():
        cfg = GitHubIntegrationService._github_cfg()
        if cfg.get("enabled"):
            return bool(cfg.get("token") and cfg.get("repo"))
        return bool(getattr(settings, "GITHUB_TOKEN", "") and getattr(settings, "GITHUB_REPO", ""))

    @classmethod
    def configured_labels(cls) -> list[str]:
        cfg = cls._github_cfg()
        raw = cfg.get("labels") or getattr(settings, "GITHUB_LABELS", "")
        if raw:
            return [label.strip() for label in str(raw).split(",") if label.strip()]
        return []

    @classmethod
    def _resolve_gurukulam_id(cls, feedback: Feedback, cfg: dict) -> str:
        branch = getattr(feedback, "branch", None)
        if branch and getattr(branch, "code", None):
            return branch.code
        return (cfg.get("gurukulam_id") or "PLATFORM").strip()

    @classmethod
    def create_issue(cls, feedback: Feedback, analysis: FeedbackAnalysis) -> tuple[GitHubIssueMapping | None, GitHubSyncResult]:
        cfg = cls._github_cfg()
        repo = (cfg.get("repo") or getattr(settings, "GITHUB_REPO", "")).strip()
        api_url = cfg.get("api_url") or getattr(settings, "GITHUB_API_URL", "https://api.github.com")
        result = GitHubSyncResult(attempted=True)

        if not cls.is_enabled():
            result.mode = "STUB"
            result.success = True
            result.messages.append(IntegrationMessage(
                level="warning",
                code="github_stub_mode",
                text="GitHub is not configured (GITHUB_TOKEN / GITHUB_REPO). A local demo issue record was saved — nothing was created in GitHub.",
            ))
            logger.info("[GitHub stub] Would create issue for %s", feedback.feedback_number)
            mapping = GitHubIssueMapping.objects.create(
                feedback=feedback,
                issue_number=abs(hash(feedback.feedback_number)) % 90000 + 10000,
                issue_url=f"https://github.com/{repo or 'your-org/your-repo'}/issues/demo",
                repo=repo or "not-configured",
                labels=cls._labels(feedback, analysis),
                state="open",
                sync_mode=GitHubIssueMapping.SyncMode.STUB,
                milestone=cfg.get("milestone", ""),
                project_node_id=cfg.get("project_node_id", ""),
            )
            result.issue_number = mapping.issue_number
            result.issue_url = mapping.issue_url
            return mapping, result

        import requests

        title = f"[{feedback.source_module}] {feedback.title}"
        body = analysis.github_issue_draft
        labels = cls._labels(feedback, analysis)
        token = (cfg.get("token") or settings.GITHUB_TOKEN).strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{api_url}/repos/{repo}/issues"
        payload = build_issue_create_payload(
            cfg, api_url=api_url, repo=repo, token=token, title=title, body=body, labels=labels,
        )

        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result.http_status = response.status_code
        result.mode = "REAL"

        if response.status_code == 422 and labels:
            result.messages.append(IntegrationMessage(
                level="warning",
                code="github_labels_retry",
                text=f"GitHub rejected labels {labels} ({parse_github_error(response)}). Retrying without labels.",
            ))
            retry_payload = build_issue_create_payload(
                cfg, api_url=api_url, repo=repo, token=token, title=title, body=body, labels=[],
            )
            response = requests.post(url, headers=headers, json=retry_payload, timeout=20)
            result.http_status = response.status_code

        if response.status_code == 201:
            data = response.json()
            metadata, enrich_messages = enrich_created_issue(
                cfg,
                api_url=api_url,
                repo=repo,
                token=token,
                issue_data=data,
                feedback_title=feedback.title,
                feedback_number=feedback.feedback_number,
                gurukulam_id=cls._resolve_gurukulam_id(feedback, cfg),
            )
            result.messages.extend(enrich_messages)
            mapping = GitHubIssueMapping.objects.create(
                feedback=feedback,
                issue_number=data["number"],
                issue_url=data["html_url"],
                repo=repo,
                labels=data.get("labels", []),
                sync_mode=GitHubIssueMapping.SyncMode.REAL,
                http_status=201,
                branch_name=metadata.get("branch_name", ""),
                milestone=metadata.get("milestone", ""),
                project_node_id=metadata.get("project_node_id", ""),
            )
            result.success = True
            result.issue_number = data["number"]
            result.issue_url = data["html_url"]
            result.messages.append(IntegrationMessage(
                level="info",
                code="github_created",
                text=f"GitHub issue #{data['number']} created successfully in {repo}.",
            ))
            return mapping, result

        error = parse_github_error(response)
        result.mode = "FAILED"
        result.success = False
        result.error = error
        result.response_body = response.text[:2000]
        hint = github_issue_create_hint(response.status_code, repo)
        result.messages.append(IntegrationMessage(
            level="error",
            code="github_api_failed",
            text=f"GitHub API returned HTTP {response.status_code}: {error}",
        ))
        if hint:
            result.messages.append(IntegrationMessage(
                level="error",
                code="github_issues_write_missing",
                text=hint,
            ))
        logger.error("GitHub issue creation failed for %s: %s %s", feedback.feedback_number, response.status_code, error)
        return None, result

    @classmethod
    def test_connection(cls) -> GitHubSyncResult:
        """Verify token, repository access, and issue-creation permission."""
        cfg = getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("github", {})
        repo = (cfg.get("repo") or getattr(settings, "GITHUB_REPO", "")).strip()
        api_url = cfg.get("api_url") or getattr(settings, "GITHUB_API_URL", "https://api.github.com")
        result = GitHubSyncResult(attempted=True)

        if not cls.is_enabled():
            result.mode = "DISABLED"
            result.messages.append(IntegrationMessage(
                level="warning",
                code="github_not_configured",
                text="Set GITHUB_ENABLED=true, GITHUB_TOKEN, and GITHUB_REPO in backend/.env",
            ))
            return result

        import requests

        token = (cfg.get("token") or settings.GITHUB_TOKEN).strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        response = requests.get(f"{api_url}/repos/{repo}", headers=headers, timeout=20)
        result.http_status = response.status_code
        if response.status_code != 200:
            result.mode = "FAILED"
            result.error = parse_github_error(response)
            result.messages.append(IntegrationMessage(
                level="error",
                code="github_repo_failed",
                text=f"GitHub repo check failed (HTTP {response.status_code}): {result.error}",
            ))
            return result

        data = response.json()
        result.mode = "REAL"
        result.messages.append(IntegrationMessage(
            level="info",
            code="github_repo_ok",
            text=f"Connected to GitHub repo {data.get('full_name', repo)}.",
        ))

        # Probe issue-write permission without creating an issue (empty title → 422 if allowed).
        probe = requests.post(
            f"{api_url}/repos/{repo}/issues",
            headers=headers,
            json={"title": "", "body": ""},
            timeout=20,
        )
        if probe.status_code in {201, 422}:
            result.success = True
            result.messages.append(IntegrationMessage(
                level="info",
                code="github_issues_write_ok",
                text="Token has permission to create GitHub issues.",
            ))
        elif probe.status_code == 404:
            result.success = False
            hint = github_issue_create_hint(404, repo)
            result.error = parse_github_error(probe)
            result.messages.append(IntegrationMessage(
                level="error",
                code="github_issues_write_missing",
                text=hint,
            ))
        else:
            result.success = False
            result.error = parse_github_error(probe)
            result.messages.append(IntegrationMessage(
                level="error",
                code="github_issues_probe_failed",
                text=f"Issue permission check failed (HTTP {probe.status_code}): {result.error}",
            ))
        return result

    @staticmethod
    def _labels(feedback: Feedback, analysis: FeedbackAnalysis) -> list[str]:
        configured = GitHubIntegrationService.configured_labels()
        if configured:
            return configured

        labels: list[str] = []
        cat = analysis.ai_category or feedback.category
        label_map = {
            FeedbackCategory.BUG: "bug",
            FeedbackCategory.FEATURE: "feature",
            FeedbackCategory.IMPROVEMENT: "enhancement",
            FeedbackCategory.PERFORMANCE: "performance",
            FeedbackCategory.SECURITY: "security",
        }
        if cat in label_map:
            labels.append(label_map[cat])
        return labels


class FeedbackWorkflowService:
    @classmethod
    def _workflow_messages(cls, feedback, analysis, github_sync: GitHubSyncResult | None = None) -> list[IntegrationMessage]:
        messages: list[IntegrationMessage] = [
            IntegrationMessage(level="info", code="feedback_saved", text=f"Feedback {feedback.feedback_number} saved."),
        ]
        if feedback.status == FeedbackStatus.DUPLICATE_LINKED:
            messages.append(IntegrationMessage(
                level="warning",
                code="duplicate_linked",
                text=f"Linked to duplicate feedback {feedback.duplicate_of.feedback_number}.",
            ))
        elif feedback.status == FeedbackStatus.PENDING_APPROVAL:
            messages.append(IntegrationMessage(
                level="warning",
                code="github_pending_approval",
                text="AI recommends a GitHub issue. Approve it in Dev Feedback Ops, or set FEEDBACK_AUTO_CREATE_ISSUE=true in .env.",
            ))
        elif feedback.status == FeedbackStatus.CLOSED and feedback.category == FeedbackCategory.APPRECIATION:
            messages.append(IntegrationMessage(level="info", code="appreciation_closed", text="Appreciation feedback auto-closed."))
        elif feedback.status == FeedbackStatus.AI_ANALYZED and analysis and not analysis.create_github_issue:
            messages.append(IntegrationMessage(
                level="info",
                code="no_github_recommended",
                text="Appreciation feedback — no GitHub issue needed.",
            ))

        auto_github = getattr(settings, "FEEDBACK_AUTO_CREATE_ISSUE", getattr(settings, "FEEDBACK_AUTO_GITHUB", False))
        if not auto_github and analysis and analysis.create_github_issue and feedback.status != FeedbackStatus.GITHUB_CREATED:
            messages.append(IntegrationMessage(
                level="info",
                code="auto_github_disabled",
                text="FEEDBACK_AUTO_CREATE_ISSUE is false — GitHub issues require manual approval unless severity is CRITICAL.",
            ))

        if github_sync:
            messages.extend(github_sync.messages)
        return messages

    @classmethod
    def record_history(cls, feedback, from_status, to_status, actor=None, reason=""):
        FeedbackHistory.objects.create(
            feedback=feedback,
            from_status=from_status or "",
            to_status=to_status,
            changed_by=actor,
            reason=reason,
        )

    @classmethod
    @transaction.atomic
    def submit_and_process(cls, feedback: Feedback, actor=None) -> tuple[Feedback, list[IntegrationMessage], GitHubSyncResult | None]:
        github_sync = None
        analysis = FeedbackAnalysisService.analyze(feedback)
        feedback.severity = analysis.raw_analysis.get("severity", feedback.severity)
        feedback.priority = analysis.recommended_priority or feedback.priority
        feedback.category = analysis.ai_category or feedback.category
        feedback.source_module = analysis.raw_analysis.get("module", feedback.source_module)
        feedback.assigned_team = analysis.recommended_team
        feedback.status = FeedbackStatus.AI_ANALYZED
        feedback.save(update_fields=[
            "severity", "priority", "category", "source_module", "assigned_team", "status", "updated_at",
        ])
        cls.record_history(feedback, FeedbackStatus.SUBMITTED, FeedbackStatus.AI_ANALYZED, actor, "AI analysis completed")

        duplicate = DuplicateDetectionService.find_duplicate(feedback)
        if duplicate:
            feedback.duplicate_of = duplicate
            feedback.status = FeedbackStatus.DUPLICATE_LINKED
            feedback.save(update_fields=["duplicate_of", "status", "updated_at"])
            cls.record_history(feedback, FeedbackStatus.AI_ANALYZED, FeedbackStatus.DUPLICATE_LINKED, actor, f"Linked to {duplicate.feedback_number}")
            return feedback, cls._workflow_messages(feedback, analysis), None

        auto_github = getattr(settings, "FEEDBACK_AUTO_CREATE_ISSUE", getattr(settings, "FEEDBACK_AUTO_GITHUB", False))
        if analysis.create_github_issue and (auto_github or feedback.severity == FeedbackSeverity.CRITICAL):
            _, github_sync = cls.create_github_issue(feedback, actor)
        elif analysis.create_github_issue:
            feedback.status = FeedbackStatus.PENDING_APPROVAL
            feedback.save(update_fields=["status", "updated_at"])
            cls.record_history(feedback, FeedbackStatus.AI_ANALYZED, FeedbackStatus.PENDING_APPROVAL, actor, "Awaiting manual approval for GitHub issue")
        elif feedback.category == FeedbackCategory.APPRECIATION:
            feedback.status = FeedbackStatus.CLOSED
            feedback.save(update_fields=["status", "updated_at"])
            cls.record_history(feedback, FeedbackStatus.AI_ANALYZED, FeedbackStatus.CLOSED, actor, "Appreciation auto-closed")

        cls._notify_reporter(feedback, analysis)
        from apps.feedback.integrations import SlackIntegrationService

        SlackIntegrationService.notify(
            f"New feedback {feedback.feedback_number} [{feedback.priority}]: {feedback.title}",
            event="submit",
        )
        return feedback, cls._workflow_messages(feedback, analysis, github_sync), github_sync

    @classmethod
    @transaction.atomic
    def create_github_issue(cls, feedback: Feedback, actor=None) -> tuple[GitHubIssueMapping | None, GitHubSyncResult]:
        analysis = feedback.analysis
        if not analysis:
            sync = GitHubSyncResult(attempted=True, mode="FAILED", success=False, error="AI analysis missing")
            sync.messages.append(IntegrationMessage(level="error", code="no_analysis", text="AI analysis required before creating GitHub issue."))
            return None, sync
        mapping, sync = GitHubIntegrationService.create_issue(feedback, analysis)
        if mapping:
            from_status = feedback.status
            feedback.status = FeedbackStatus.GITHUB_CREATED
            feedback.save(update_fields=["status", "updated_at"])
            cls.record_history(feedback, from_status, FeedbackStatus.GITHUB_CREATED, actor, f"GitHub #{mapping.issue_number}")
            from apps.feedback.integrations import SlackIntegrationService

            SlackIntegrationService.notify(
                f"Feedback {feedback.feedback_number} → GitHub issue #{mapping.issue_number}: {feedback.title}",
                event="issue_created",
            )
        elif sync.error:
            cls.record_history(
                feedback,
                feedback.status,
                feedback.status,
                actor,
                f"GitHub failed (HTTP {sync.http_status}): {sync.error[:300]}",
            )
        return mapping, sync

    @classmethod
    @transaction.atomic
    def update_status(cls, feedback: Feedback, new_status: str, actor, reason=""):
        old = feedback.status
        feedback.status = new_status
        feedback.save(update_fields=["status", "updated_at"])
        cls.record_history(feedback, old, new_status, actor, reason)
        if new_status == FeedbackStatus.CLOSED:
            cls._notify_reporter(feedback, getattr(feedback, "analysis", None), closed=True)
        return feedback

    @classmethod
    def _notify_reporter(cls, feedback: Feedback, analysis=None, closed=False):
        email = feedback.reporter_email or (feedback.reporter.email if feedback.reporter else "")
        if not email:
            return
        from apps.notifications.services import NotificationDispatcher

        if closed:
            body_key = "feedback_closed"
        else:
            body_key = "feedback_received"
        NotificationDispatcher.send(
            template_code="DONATION_RECEIPT",
            recipient_email=email,
            context={
                "donor_name": feedback.reporter_type or "User",
                "amount": feedback.feedback_number,
                "receipt_number": feedback.status,
                "category": analysis.ai_summary if analysis else feedback.title,
            },
            idempotency_key=f"feedback-{feedback.id}-{feedback.status}",
            channels=["EMAIL"],
        )
