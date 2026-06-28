"use client";

import { useEffect, useState } from "react";

import { IntegrationMessages, type IntegrationMessage } from "@/components/IntegrationMessages";
import { PageHeader } from "@/components/PageHeader";
import {
  approveGitHubIssue,
  fetchFeedbackDetail,
  fetchFeedbackIntegrations,
  fetchFeedbackList,
  fetchFeedbackStats,
  testGitHubConnection,
  updateFeedbackStatus,
  type FeedbackItem,
} from "@/lib/feedback";

export default function FeedbackOpsPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [stats, setStats] = useState<Awaited<ReturnType<typeof fetchFeedbackStats>> | null>(null);
  const [integrations, setIntegrations] = useState<Awaited<ReturnType<typeof fetchFeedbackIntegrations>> | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof fetchFeedbackDetail>> | null>(null);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<IntegrationMessage[]>([]);
  const [testingGitHub, setTestingGitHub] = useState(false);

  const load = async () => {
    const [list, s, cfg] = await Promise.all([
      fetchFeedbackList(),
      fetchFeedbackStats(),
      fetchFeedbackIntegrations().catch(() => null),
    ]);
    setItems(list);
    setStats(s);
    setIntegrations(cfg);
  };

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load queue"));
  }, []);

  useEffect(() => {
    if (selected) fetchFeedbackDetail(selected).then(setDetail).catch(() => setDetail(null));
    else setDetail(null);
  }, [selected]);

  const onTestGitHub = async () => {
    setTestingGitHub(true);
    setMessages([]);
    try {
      const result = await testGitHubConnection();
      setMessages(result.github_sync.messages ?? []);
      if (!result.success) setError("GitHub connection test failed — see messages below.");
      else setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub test failed");
    } finally {
      setTestingGitHub(false);
    }
  };

  const onApprove = async (id: string) => {
    setMessages([]);
    setError("");
    try {
      const result = await approveGitHubIssue(id);
      setMessages(result.messages);
      await load();
      if (selected === id) fetchFeedbackDetail(id).then(setDetail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub approval failed");
    }
  };

  const onStatus = async (id: string, status: string) => {
    await updateFeedbackStatus(id, status);
    await load();
    if (selected === id) fetchFeedbackDetail(id).then(setDetail);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dev feedback ops center"
        description="Triage application feedback, approve GitHub issues, and monitor integration responses."
      />

      <section className="rounded-xl border bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-stone-900">Integration config</h2>
          <button
            type="button"
            disabled={testingGitHub}
            onClick={onTestGitHub}
            className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs font-medium hover:bg-stone-50 disabled:opacity-60"
          >
            {testingGitHub ? "Testing…" : "Test GitHub connection"}
          </button>
        </div>

        {integrations ? (
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs">
              <p className="font-semibold text-stone-800">General</p>
              <dl className="mt-2 space-y-1 text-stone-600">
                <div className="flex justify-between gap-2">
                  <dt>Tracker</dt>
                  <dd className="font-medium text-stone-800">{integrations.issue_tracker}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Auto-create issue</dt>
                  <dd className="font-medium text-stone-800">{integrations.auto_create_issue ? "on" : "off"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Default env</dt>
                  <dd className="font-medium text-stone-800">{integrations.default_env}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs">
              <p className="font-semibold text-stone-800">GitHub</p>
              <dl className="mt-2 space-y-1 text-stone-600">
                <div className="flex justify-between gap-2">
                  <dt>Status</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.configured ? "configured" : "not configured"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Repo</dt>
                  <dd className="truncate font-medium text-stone-800">{integrations.providers.github.repo ?? "—"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Labels</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.labels.length
                      ? integrations.providers.github.labels.join(", ")
                      : "category defaults"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Milestone</dt>
                  <dd className="font-medium text-stone-800">{integrations.providers.github.milestone ?? "—"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Project</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.project_configured ? "linked" : "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Assignee</dt>
                  <dd className="font-medium text-stone-800">manual</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs">
              <p className="font-semibold text-stone-800">GitHub branches</p>
              <dl className="mt-2 space-y-1 text-stone-600">
                <div className="flex justify-between gap-2">
                  <dt>Auto-create branch</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.auto_create_branch ? "on" : "off"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Base branch</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.default_branch ?? "repo default"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Branch prefix</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.branch_prefix || "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt>Pattern</dt>
                  <dd className="font-medium text-stone-800">
                    {integrations.providers.github.branch_prefix ?? ""}
                    {"{issue#}-{slug}"}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-stone-500">Loading integration config…</p>
        )}

        <div className="mt-4">
          <IntegrationMessages messages={messages} />
        </div>
      </section>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {stats ? (
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Total</p>
            <p className="text-2xl font-bold">{stats.total}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Pending GitHub</p>
            <p className="text-2xl font-bold text-amber-600">{stats.pending_github_approval}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">In progress</p>
            <p className="text-2xl font-bold">{stats.by_status?.IN_PROGRESS ?? 0}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Closed</p>
            <p className="text-2xl font-bold text-green-700">{stats.by_status?.CLOSED ?? 0}</p>
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Feedback queue</h2>
          <ul className="mt-4 max-h-[32rem] divide-y overflow-y-auto text-sm">
            {items.length === 0 ? (
              <li className="py-6 text-center text-stone-500">No feedback in queue yet.</li>
            ) : null}
            {items.map((fb) => (
              <li key={fb.id}>
                <button type="button" onClick={() => setSelected(fb.id)} className="w-full py-3 text-left hover:bg-stone-50">
                  <p className="font-medium">{fb.feedback_number} · {fb.title}</p>
                  <p className="text-xs text-stone-500">
                    {fb.source_module} · {fb.status} · {fb.priority}
                    {fb.github_issue?.sync_mode === "STUB" ? " · demo GitHub" : ""}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border bg-white p-5">
          {detail ? (
            <div className="space-y-4 text-sm">
              <h2 className="font-semibold">{detail.feedback.title}</h2>
              <p className="text-stone-600">{detail.feedback.description}</p>
              {detail.feedback.analysis ? (
                <div className="rounded-lg bg-stone-50 p-4">
                  <p className="font-medium">AI analysis ({detail.feedback.analysis.confidence}% confidence)</p>
                  <p className="mt-1">{detail.feedback.analysis.ai_summary}</p>
                  {detail.feedback.analysis.create_github_issue ? (
                    <p className="mt-2 text-xs text-amber-700">AI recommends creating a GitHub issue.</p>
                  ) : null}
                </div>
              ) : null}
              {detail.feedback.github_issue ? (
                <div className="space-y-1">
                  {detail.feedback.github_issue.sync_mode === "REAL" ? (
                    <a href={detail.feedback.github_issue.issue_url} className="text-saffron-700 hover:underline">
                      GitHub #{detail.feedback.github_issue.issue_number}
                    </a>
                  ) : (
                    <p className="text-amber-800">
                      Demo record #{detail.feedback.github_issue.issue_number} — not in GitHub ({detail.feedback.github_issue.sync_mode}).
                      {detail.feedback.github_issue.api_error ? ` Error: ${detail.feedback.github_issue.api_error}` : ""}
                    </p>
                  )}
                  {detail.feedback.github_issue.branch_name ? (
                    <p className="text-xs text-stone-600">
                      Branch: <code className="rounded bg-stone-100 px-1">{detail.feedback.github_issue.branch_name}</code>
                    </p>
                  ) : null}
                  {detail.feedback.github_issue.milestone ? (
                    <p className="text-xs text-stone-600">Milestone: {detail.feedback.github_issue.milestone}</p>
                  ) : null}
                </div>
              ) : !detail.feedback.github_issue ? (
                <div className="space-y-2">
                  <button type="button" onClick={() => onApprove(detail.feedback.id)} className="rounded-lg bg-saffron-600 px-3 py-1.5 text-xs font-semibold text-white">
                    Create GitHub issue
                  </button>
                  <p className="text-xs text-stone-500">No GitHub issue linked yet. Click to create one in your configured repo.</p>
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {["IN_PROGRESS", "TESTING", "RELEASED", "CLOSED"].map((s) => (
                  <button key={s} type="button" onClick={() => onStatus(detail.feedback.id, s)} className="rounded border px-2 py-1 text-xs hover:bg-stone-50">
                    → {s.replace("_", " ")}
                  </button>
                ))}
              </div>
              <div>
                <p className="font-medium">History</p>
                <ul className="mt-2 text-xs text-stone-500">
                  {detail.history.map((h, i) => (
                    <li key={i}>{h.occurred_at}: {h.from_status} → {h.to_status} {h.reason && `(${h.reason})`}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-stone-500">Select feedback to triage.</p>
          )}
        </section>
      </div>
    </div>
  );
}
