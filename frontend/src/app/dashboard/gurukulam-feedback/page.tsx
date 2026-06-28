"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import {
  fetchGurukulamFeedbackDetail,
  fetchGurukulamFeedbackList,
  fetchGurukulamFeedbackStats,
  GURUKULAM_CATEGORY_LABELS,
  updateGurukulamFeedbackStatus,
  type GurukulamFeedbackItem,
} from "@/lib/gurukulamFeedback";

export default function GurukulamFeedbackAdminPage() {
  const [items, setItems] = useState<GurukulamFeedbackItem[]>([]);
  const [stats, setStats] = useState<Awaited<ReturnType<typeof fetchGurukulamFeedbackStats>> | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof fetchGurukulamFeedbackDetail>> | null>(null);
  const [response, setResponse] = useState("");

  const load = async () => {
    const [list, s] = await Promise.all([fetchGurukulamFeedbackList(), fetchGurukulamFeedbackStats()]);
    setItems(list);
    setStats(s);
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (selected) fetchGurukulamFeedbackDetail(selected).then(setDetail).catch(() => setDetail(null));
    else setDetail(null);
  }, [selected]);

  const onStatus = async (id: string, status: string) => {
    await updateGurukulamFeedbackStatus(id, status, response);
    setResponse("");
    await load();
    if (selected === id) fetchGurukulamFeedbackDetail(id).then(setDetail);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Gurukulam feedback review"
        description="Institutional feedback from students, parents, and community. Not routed to GitHub or DevOps."
      />

      {stats ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Total</p>
            <p className="text-2xl font-bold">{stats.total}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Pending review</p>
            <p className="text-2xl font-bold text-amber-600">{stats.pending_review}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Closed</p>
            <p className="text-2xl font-bold text-green-700">{stats.by_status?.CLOSED ?? 0}</p>
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Submissions</h2>
          <ul className="mt-4 max-h-[32rem] divide-y overflow-y-auto text-sm">
            {items.map((fb) => (
              <li key={fb.id}>
                <button type="button" onClick={() => setSelected(fb.id)} className="w-full py-3 text-left hover:bg-stone-50">
                  <p className="font-medium">{fb.feedback_number} · {fb.title}</p>
                  <p className="text-xs text-stone-500">
                    {GURUKULAM_CATEGORY_LABELS[fb.category] ?? fb.category} · {fb.status.replace(/_/g, " ")}
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
              <textarea
                rows={3}
                className="w-full rounded-lg border px-3 py-2 text-sm"
                placeholder="Admin response to the reporter"
                value={response}
                onChange={(e) => setResponse(e.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                {["UNDER_REVIEW", "RESPONDED", "CLOSED"].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => onStatus(detail.feedback.id, s)}
                    className="rounded border px-2 py-1 text-xs hover:bg-stone-50"
                  >
                    → {s.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
              {detail.feedback.admin_response ? (
                <p className="rounded-lg bg-stone-50 p-3 text-stone-700">{detail.feedback.admin_response}</p>
              ) : null}
            </div>
          ) : (
            <p className="text-stone-500">Select feedback to review.</p>
          )}
        </section>
      </div>
    </div>
  );
}
