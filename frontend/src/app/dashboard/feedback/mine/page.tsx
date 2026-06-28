"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { fetchFeedbackList, type FeedbackItem } from "@/lib/feedback";

export default function MyFeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchFeedbackList()
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load feedback"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My feedback"
        description="Track the status of feedback you have submitted."
      />

      {loading ? <p className="text-sm text-stone-500">Loading…</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {!loading && !error && items.length === 0 ? (
        <div className="rounded-xl border bg-white p-8 text-center">
          <p className="text-stone-600">You have not submitted any feedback yet.</p>
          <Link href="/dashboard/feedback/submit" className="mt-4 inline-block text-sm font-medium text-saffron-700 hover:underline">
            Submit feedback →
          </Link>
        </div>
      ) : null}

      <ul className="divide-y rounded-xl border bg-white">
        {items.map((fb) => (
          <li key={fb.id} className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-stone-900">{fb.title}</p>
                <p className="mt-1 text-xs text-stone-500">
                  {fb.feedback_number} · {fb.source_module} · {fb.status.replace(/_/g, " ")} · {fb.priority}
                </p>
              </div>
              {fb.github_issue ? (
                <a href={fb.github_issue.issue_url} className="text-xs text-saffron-700 hover:underline">
                  GitHub #{fb.github_issue.issue_number}
                </a>
              ) : null}
            </div>
            <p className="mt-2 text-sm text-stone-600 line-clamp-2">{fb.description}</p>
            {fb.analysis ? (
              <p className="mt-2 text-xs text-stone-500">AI: {fb.analysis.ai_summary}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
