"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import {
  fetchGurukulamFeedbackList,
  GURUKULAM_CATEGORY_LABELS,
  type GurukulamFeedbackItem,
} from "@/lib/gurukulamFeedback";

export default function PortalMyGurukulamFeedbackPage() {
  const [items, setItems] = useState<GurukulamFeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGurukulamFeedbackList()
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader title="My Gurukulam feedback" description="Track responses from the administration team." />
      {loading ? <p className="text-sm text-stone-500">Loading…</p> : null}
      {!loading && items.length === 0 ? (
        <p className="text-sm text-stone-600">
          No submissions yet. <Link href="/portal/feedback" className="text-saffron-700 hover:underline">Submit feedback</Link>
        </p>
      ) : null}
      <ul className="divide-y rounded-xl border bg-white">
        {items.map((fb) => (
          <li key={fb.id} className="p-4">
            <p className="font-medium">{fb.feedback_number} · {fb.title}</p>
            <p className="text-xs text-stone-500">
              {fb.status.replace(/_/g, " ")} · {GURUKULAM_CATEGORY_LABELS[fb.category] ?? fb.category}
            </p>
            {fb.admin_response ? (
              <p className="mt-2 rounded-lg bg-stone-50 p-3 text-sm text-stone-700">
                <span className="font-medium">Response: </span>
                {fb.admin_response}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
