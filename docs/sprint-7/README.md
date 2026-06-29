# Sprint 7: Feedback Platform (Two Modules)

## 1. Application Development Feedback (`apps/feedback`)

**Who:** Super Admin only  
**Purpose:** Platform bugs, enhancements, performance — routed to AI + GitHub/DevOps  
**API:** `/api/v1/feedback/`

## 2. Gurukulam Feedback (`apps/gurukulam_feedback`)

**Who:** Students, parents, acharyas, donors, alumni, wardens, visitors (anonymous optional)  
**Purpose:** Institutional feedback — teaching, facilities, events, suggestions  
**Never** creates GitHub issues or DevOps tickets  
**API:** `/api/v1/gurukulam-feedback/`

## Architecture (Dev feedback only)

```
User → Feedback API → AI Analysis → Duplicate Detection → Workflow Engine → GitHub Issue → Notify Reporter
```

## Models

| Model | Purpose |
|-------|---------|
| `Feedback` | Core submission with environment, platform, module context |
| `FeedbackAttachment` | Screenshots / files (S3) |
| `FeedbackAnalysis` | AI sentiment, category, priority, GitHub draft |
| `FeedbackHistory` | Append-only status transitions |
| `FeedbackComment` | Internal / reporter comments |
| `GitHubIssueMapping` | Linked GitHub issue number & URL |

## API

| Method | Path | Access |
|--------|------|--------|
| POST | `/feedback/submit/` | Public (anonymous) or authenticated |
| GET | `/feedback/` | Own submissions or all (`feedback.manage`) |
| GET | `/feedback/stats/` | Ops dashboard (`feedback.manage`) |
| GET | `/feedback/integrations/` | Integration config status (`feedback.manage`) |
| GET | `/feedback/{id}/` | Detail + history |
| POST | `/feedback/{id}/approve-github/` | Create GitHub issue |
| PATCH | `/feedback/{id}/status/` | Workflow transitions |
| POST | `/feedback/{id}/comments/` | Add comment |

## AI Pipeline (demo mode)

Keyword/heuristic classifier (production: plug external LLM via `FEEDBACK_AI_API_URL`):

1. Sentiment analysis
2. Category & module detection
3. Severity / priority prediction
4. Root cause suggestion
5. Duplicate detection (`SequenceMatcher` ≥ 72%)
6. GitHub issue draft generation
7. Auto-create or route to manual approval

## Integration configuration

All settings live in **`backend/.env`** (template: **`backend/.env.example`**).  
Django loads them via `config/feedback_integrations.py` → `FEEDBACK_INTEGRATIONS` in `config/settings/base.py`.

**View active config (no secrets):** `GET /api/v1/feedback/integrations/` — requires `feedback.manage`.

### General

```env
FEEDBACK_DEFAULT_ENV=PRODUCTION
FEEDBACK_ISSUE_TRACKER=GITHUB    # GITHUB | GITLAB | JIRA | AZURE_BOARDS
FEEDBACK_AUTO_CREATE_ISSUE=false # skip manual approval for high-confidence issues
```

### GitHub Issues

```env
GITHUB_ENABLED=false
GITHUB_TOKEN=ghp_...
GITHUB_REPO=org/repo
GITHUB_API_URL=https://api.github.com   # GitHub Enterprise: https://github.example.com/api/v3
# Optional comma-separated labels (must exist in repo)
GITHUB_LABELS=bug,feedback
# Milestone title or number — set on issue create (not assignee; assign manually in GitHub)
GITHUB_MILESTONE=Sprint 7
# GitHub Projects v2 node ID — adds issue to project after create (GraphQL)
GITHUB_PROJECT_NODE_ID=PVT_kwDO...
GITHUB_DEFAULT_BRANCH=main              # empty = repo default
GITHUB_BRANCH_PREFIX=                   # optional, e.g. feature/
GITHUB_BRANCH_NAME_TEMPLATE={issue}-{feedback_number}-{gurukulam_id}-{slug}
GITHUB_GURUKULAM_ID=PLATFORM            # fallback when feedback has no branch
GITHUB_AUTO_CREATE_BRANCH=true          # auto-create branch per issue
```

**Branch name format (default):** `{issue}-{feedback_number}-{gurukulam_id}-{slug}`  
Example: `7-FB-2026-9DD2C9-HQ-01-platform-the-branch-name-should-have-the-format-of-custom`  
`gurukulam_id` uses the feedback's `branch.code` when set; otherwise `GITHUB_GURUKULAM_ID`.

**On issue create (backend API, not GitHub UI):**

| Field | Behavior |
|-------|----------|
| Labels | From `GITHUB_LABELS` + category (`bug` / `feature`) |
| Milestone | From `GITHUB_MILESTONE` if set |
| Project | From `GITHUB_PROJECT_NODE_ID` if set |
| Assignee | **Not set** — assign manually in GitHub |
| Branch | `{issue}-{feedback_number}-{gurukulam_id}-{slug}` when `GITHUB_AUTO_CREATE_BRANCH=true` |

Token permissions: **Issues: Read and write**, **Contents: Read and write** (branch creation), and **Project** scope for Projects v2.

### GitLab Issues

```env
GITLAB_ENABLED=false
GITLAB_TOKEN=glpat-...
GITLAB_PROJECT_ID=12345
GITLAB_API_URL=https://gitlab.com/api/v4
```

### Jira

```env
JIRA_ENABLED=false
JIRA_BASE_URL=https://yourorg.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=GURU
```

### Azure Boards (Azure DevOps)

```env
AZURE_BOARDS_ENABLED=false
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=Gurukulam
AZURE_DEVOPS_PAT=...
AZURE_BOARDS_WORK_ITEM_TYPE=Bug
AZURE_DEVOPS_API_URL=https://dev.azure.com
```

### Slack notifications

```env
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-...          # optional if using webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#feedback-ops
SLACK_NOTIFY_ON_SUBMIT=false
SLACK_NOTIFY_ON_ISSUE_CREATED=true
```

Without credentials, issue trackers run in **demo/stub mode** (local issue numbers, log-only Slack).

**Currently wired:** GitHub issue creation + Slack notifications on submit/issue-created.  
GitLab, Jira, and Azure Boards clients are configured and ready (`apps/feedback/integrations.py`); routing by `FEEDBACK_ISSUE_TRACKER` is a follow-up.

## Permissions

| Permission | Roles |
|------------|-------|
| `feedback.add` | All user types |
| `feedback.view` | All user types (own only unless manage) |
| `feedback.manage` | Super Admin, Branch Admin |

## Frontend

| Route | Who | Purpose |
|-------|-----|---------|
| `/feedback` | Public | Anonymous or logged-in submit form |
| `/portal/feedback` | All authenticated users | Submit form in portal shell |
| `/portal/feedback/mine` | All authenticated users | Own submissions |
| `/dashboard/feedback/submit` | Dashboard users (`feedback.add`) | Submit form |
| `/dashboard/feedback/mine` | Dashboard users (`feedback.view`) | Own submissions |
| `/dashboard/feedback/ops` | Admins (`feedback.manage`) | Triage queue |

## Setup

```bash
python manage.py migrate
python manage.py seed_foundation   # adds feedback.* permissions
```

## Tests

```bash
python manage.py test apps.feedback.tests
```

## Future (AI Operations Center)

- Release regression detection
- Trend dashboards
- Jira/Azure DevOps sync
- LLM-backed analysis endpoint
