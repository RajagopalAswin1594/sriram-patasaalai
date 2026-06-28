"use client";

import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { getStoredTokens } from "@/lib/api";
import {
  FEEDBACK_CATEGORIES,
  FEEDBACK_CATEGORY_LABELS,
  FEEDBACK_ENVIRONMENTS,
  FEEDBACK_MODULES,
  FEEDBACK_PLATFORMS,
  defaultFeedbackForm,
  type FeedbackSubmitPayload,
} from "@/lib/feedbackForm";
import { submitFeedback, type FeedbackItem } from "@/lib/feedback";
import { IntegrationMessages, type IntegrationMessage } from "@/components/IntegrationMessages";

type Props = {
  defaultModule?: string;
  defaultScreen?: string;
  onSuccess?: (item: FeedbackItem) => void;
  showAnonymousOption?: boolean;
};

const inputClass = "w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-saffron-500 focus:outline-none focus:ring-1 focus:ring-saffron-500";
const labelClass = "mb-1 block text-sm font-medium text-stone-700";

export function FeedbackSubmitForm({
  defaultModule,
  defaultScreen,
  onSuccess,
  showAnonymousOption = true,
}: Props) {
  const { me } = useAuth();
  const [form, setForm] = useState<FeedbackSubmitPayload>(() =>
    defaultFeedbackForm({
      source_module: defaultModule ?? "PLATFORM",
      screen_name: defaultScreen ?? (typeof window !== "undefined" ? window.location.pathname : ""),
    }),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<FeedbackItem | null>(null);
  const [messages, setMessages] = useState<IntegrationMessage[]>([]);

  useEffect(() => {
    if (typeof window !== "undefined" && !form.browser_device) {
      setForm((f) => ({ ...f, browser_device: navigator.userAgent.slice(0, 255) }));
    }
  }, [form.browser_device]);

  const showBugFields = ["BUG", "PERFORMANCE", "UI_UX", "SECURITY"].includes(form.category);
  const isPublic = !me;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = getStoredTokens();
      const payload = { ...form };
      if (me && !isPublic) {
        payload.is_anonymous = false;
        payload.reporter_email = me.user.email;
      }
      const response = await submitFeedback(payload, tokens?.access);
      setResult(response.data);
      setMessages(response.messages);
      onSuccess?.(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-6">
        <h2 className="text-lg font-semibold text-green-900">Feedback received</h2>
        <p className="mt-2 text-sm text-green-800">
          Reference <strong>{result.feedback_number}</strong> · Status: {result.status.replace(/_/g, " ")}
        </p>
        <div className="mt-4">
          <IntegrationMessages messages={messages} />
        </div>
        {result.analysis ? (
          <div className="mt-4 rounded-lg border border-green-100 bg-white p-4 text-sm">
            <p className="font-medium text-stone-900">AI analysis</p>
            <p className="mt-1 text-stone-600">{result.analysis.ai_summary}</p>
            <p className="mt-2 text-xs text-stone-500">
              Priority {result.analysis.recommended_priority} · Confidence {result.analysis.confidence}%
            </p>
          </div>
        ) : null}
        {result.github_issue ? (
          <div className="mt-3 space-y-1">
            {result.github_issue.sync_mode === "REAL" ? (
              <a href={result.github_issue.issue_url} className="inline-block text-sm text-saffron-700 hover:underline">
                GitHub issue #{result.github_issue.issue_number}
              </a>
            ) : (
              <p className="text-sm text-amber-800">
                Demo GitHub record #{result.github_issue.issue_number} — not created in GitHub ({result.github_issue.sync_mode}).
              </p>
            )}
            {result.github_issue.branch_name ? (
              <p className="text-xs text-stone-600">Branch: {result.github_issue.branch_name}</p>
            ) : null}
          </div>
        ) : null}
        <button
          type="button"
          onClick={() => {
            setResult(null);
            setMessages([]);
            setForm(defaultFeedbackForm({ source_module: defaultModule ?? form.source_module }));
          }}
          className="mt-4 text-sm font-medium text-saffron-700 hover:underline"
        >
          Submit another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {me ? (
        <p className="rounded-lg bg-stone-50 px-4 py-3 text-sm text-stone-600">
          Submitting as <strong>{me.user.profile?.display_name || me.user.email}</strong> ({me.user.user_type})
        </p>
      ) : null}

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h3 className="font-semibold text-stone-900">What happened?</h3>
        <div>
          <label className={labelClass} htmlFor="fb-title">Title *</label>
          <input
            id="fb-title"
            required
            className={inputClass}
            placeholder="Short summary of the issue or suggestion"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
        </div>
        <div>
          <label className={labelClass} htmlFor="fb-description">Description *</label>
          <textarea
            id="fb-description"
            required
            rows={4}
            className={inputClass}
            placeholder="Describe the issue, request, or feedback in detail"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
      </section>

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h3 className="font-semibold text-stone-900">Classification</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="fb-category">Category</label>
            <select
              id="fb-category"
              className={inputClass}
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            >
              {FEEDBACK_CATEGORIES.map((c) => (
                <option key={c} value={c}>{FEEDBACK_CATEGORY_LABELS[c] ?? c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="fb-module">Module</label>
            <select
              id="fb-module"
              className={inputClass}
              value={form.source_module}
              onChange={(e) => setForm((f) => ({ ...f, source_module: e.target.value }))}
            >
              {FEEDBACK_MODULES.map((m) => (
                <option key={m} value={m}>{m.replace("_", " ")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="fb-environment">Environment</label>
            <select
              id="fb-environment"
              className={inputClass}
              value={form.environment}
              onChange={(e) => setForm((f) => ({ ...f, environment: e.target.value }))}
            >
              {FEEDBACK_ENVIRONMENTS.map((env) => (
                <option key={env} value={env}>{env}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="fb-platform">Platform</label>
            <select
              id="fb-platform"
              className={inputClass}
              value={form.platform}
              onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}
            >
              {FEEDBACK_PLATFORMS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h3 className="font-semibold text-stone-900">Context</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="fb-screen">Screen / page</label>
            <input
              id="fb-screen"
              className={inputClass}
              placeholder="/portal/student/lessons"
              value={form.screen_name}
              onChange={(e) => setForm((f) => ({ ...f, screen_name: e.target.value }))}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="fb-version">App version</label>
            <input
              id="fb-version"
              className={inputClass}
              placeholder="1.0.0"
              value={form.app_version}
              onChange={(e) => setForm((f) => ({ ...f, app_version: e.target.value }))}
            />
          </div>
        </div>
        <div>
          <label className={labelClass} htmlFor="fb-device">Browser / device</label>
          <input
            id="fb-device"
            className={inputClass}
            value={form.browser_device}
            onChange={(e) => setForm((f) => ({ ...f, browser_device: e.target.value }))}
          />
        </div>
      </section>

      {showBugFields ? (
        <section className="space-y-4 rounded-xl border bg-white p-5">
          <h3 className="font-semibold text-stone-900">Bug details</h3>
          <div>
            <label className={labelClass} htmlFor="fb-steps">Steps to reproduce</label>
            <textarea
              id="fb-steps"
              rows={3}
              className={inputClass}
              placeholder="1. Go to… 2. Click… 3. See error"
              value={form.steps_to_reproduce}
              onChange={(e) => setForm((f) => ({ ...f, steps_to_reproduce: e.target.value }))}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="fb-expected">Expected result</label>
              <textarea
                id="fb-expected"
                rows={2}
                className={inputClass}
                value={form.expected_result}
                onChange={(e) => setForm((f) => ({ ...f, expected_result: e.target.value }))}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="fb-actual">Actual result</label>
              <textarea
                id="fb-actual"
                rows={2}
                className={inputClass}
                value={form.actual_result}
                onChange={(e) => setForm((f) => ({ ...f, actual_result: e.target.value }))}
              />
            </div>
          </div>
        </section>
      ) : null}

      {isPublic && showAnonymousOption ? (
        <section className="space-y-4 rounded-xl border bg-white p-5">
          <h3 className="font-semibold text-stone-900">Contact (optional)</h3>
          <div>
            <label className={labelClass} htmlFor="fb-email">Your email</label>
            <input
              id="fb-email"
              type="email"
              className={inputClass}
              placeholder="you@example.com"
              value={form.reporter_email}
              onChange={(e) => setForm((f) => ({ ...f, reporter_email: e.target.value }))}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-stone-700">
            <input
              type="checkbox"
              checked={form.is_anonymous}
              onChange={(e) => setForm((f) => ({ ...f, is_anonymous: e.target.checked }))}
            />
            Submit anonymously
          </label>
        </section>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-saffron-600 py-3 text-sm font-semibold text-white hover:bg-saffron-700 disabled:opacity-60"
      >
        {loading ? "Submitting…" : "Submit feedback"}
      </button>
    </form>
  );
}
