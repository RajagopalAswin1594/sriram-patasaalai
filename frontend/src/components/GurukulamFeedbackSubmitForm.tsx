"use client";

import { FormEvent, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { getStoredTokens } from "@/lib/api";
import {
  GURUKULAM_CATEGORIES,
  GURUKULAM_CATEGORY_LABELS,
  submitGurukulamFeedback,
  type GurukulamFeedbackItem,
} from "@/lib/gurukulamFeedback";

const inputClass =
  "w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-saffron-500 focus:outline-none focus:ring-1 focus:ring-saffron-500";
const labelClass = "mb-1 block text-sm font-medium text-stone-700";

export function GurukulamFeedbackSubmitForm() {
  const { me } = useAuth();
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "SUGGESTION",
    reporter_email: "",
    is_anonymous: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<GurukulamFeedbackItem | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = getStoredTokens();
      const data = await submitGurukulamFeedback(form, tokens?.access);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-6">
        <h2 className="text-lg font-semibold text-green-900">Thank you for your feedback</h2>
        <p className="mt-2 text-sm text-green-800">
          Reference <strong>{result.feedback_number}</strong>. Our team will review your message.
        </p>
        <button
          type="button"
          onClick={() => {
            setResult(null);
            setForm({ title: "", description: "", category: "SUGGESTION", reporter_email: "", is_anonymous: false });
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
          Sharing feedback about Gurukulam as <strong>{me.user.profile?.display_name || me.user.email}</strong>
        </p>
      ) : (
        <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Share your thoughts about Gurukulam — teaching, facilities, programs, or suggestions. This is not a technical bug report.
        </p>
      )}

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <div>
          <label className={labelClass} htmlFor="gf-title">Subject *</label>
          <input
            id="gf-title"
            required
            className={inputClass}
            placeholder="Brief summary of your feedback"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
        </div>
        <div>
          <label className={labelClass} htmlFor="gf-category">Category</label>
          <select
            id="gf-category"
            className={inputClass}
            value={form.category}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
          >
            {GURUKULAM_CATEGORIES.map((c) => (
              <option key={c} value={c}>{GURUKULAM_CATEGORY_LABELS[c]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass} htmlFor="gf-description">Your feedback *</label>
          <textarea
            id="gf-description"
            required
            rows={5}
            className={inputClass}
            placeholder="Tell us about your experience, suggestion, or concern regarding Gurukulam"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
      </section>

      {!me ? (
        <section className="space-y-4 rounded-xl border bg-white p-5">
          <div>
            <label className={labelClass} htmlFor="gf-email">Email (optional)</label>
            <input
              id="gf-email"
              type="email"
              className={inputClass}
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
        {loading ? "Submitting…" : "Submit Gurukulam feedback"}
      </button>
    </form>
  );
}
