"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";
import { DocumentPreview } from "@/components/DocumentPreview";
import { fetchAdminApplication, reviewApplication } from "@/lib/admissions";
import type { Application, NotificationItem, StatusHistoryItem } from "@/lib/admissions";
import { ApiError } from "@/lib/api";

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { hasPermission } = useAuth();
  const [app, setApp] = useState<(Application & { status_history?: StatusHistoryItem[]; notifications?: NotificationItem[] }) | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchAdminApplication(id);
      setApp(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load application");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hasPermission("admissions.view")) load();
  }, [hasPermission, id]);

  const approve = async () => {
    await reviewApplication(id, "APPROVED");
    await load();
  };

  const reject = async () => {
    const reason = prompt("Rejection reason for applicant:") ?? "";
    await reviewApplication(id, "REJECTED", reason);
    await load();
  };

  if (loading) return <p className="text-stone-500">Loading...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!app) return null;

  const isPending = app.status === "PENDING" || app.status === "UNDER_REVIEW";

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link href="/dashboard/admissions" className="text-sm text-saffron-700 hover:underline">← Back to queue</Link>
          <h1 className="mt-2 text-2xl font-bold">{app.application_number}</h1>
          <p className="text-stone-500">{app.student_first_name} {app.student_last_name} · {app.branch_name}</p>
        </div>
        {isPending && hasPermission("admissions.approve") ? (
          <div className="flex gap-2">
            <button type="button" onClick={approve} className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white">Approve</button>
            <button type="button" onClick={reject} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white">Reject</button>
          </div>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Student</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-stone-500">DOB</dt><dd>{app.date_of_birth}</dd></div>
            <div className="flex justify-between"><dt className="text-stone-500">Grade</dt><dd>{app.grade_applying}</dd></div>
            <div className="flex justify-between"><dt className="text-stone-500">Status</dt><dd className="font-medium">{app.status}</dd></div>
          </dl>
        </section>
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Guardian (PII)</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-stone-500">Name</dt><dd>{app.parent_name}</dd></div>
            <div className="flex justify-between"><dt className="text-stone-500">Phone</dt><dd>{app.parent_phone}</dd></div>
            <div className="flex justify-between"><dt className="text-stone-500">Email</dt><dd>{app.parent_email || "—"}</dd></div>
          </dl>
          <p className="mt-3 text-xs text-stone-400">Consent recorded: {app.data_consent_at ? new Date(app.data_consent_at).toLocaleString() : "—"} ({app.data_consent_version})</p>
        </section>
      </div>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Submitted documents</h2>
        <p className="mt-1 text-xs text-stone-500">View-only preview. Approve, reject, or request resubmission with applicant notification.</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {(app.documents ?? []).length === 0 ? (
            <p className="text-sm text-stone-500">No documents submitted.</p>
          ) : (
            app.documents.map((doc) => (
              <DocumentPreview
                key={doc.id}
                applicationId={id}
                document={doc}
                canReview={isPending && hasPermission("admissions.approve")}
                onReviewed={load}
              />
            ))
          )}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Status history (audit trail)</h2>
        <ul className="mt-3 space-y-2">
          {(app.status_history ?? []).length === 0 ? (
            <li className="text-sm text-stone-500">No transitions recorded yet.</li>
          ) : (
            app.status_history!.map((h) => (
              <li key={h.id} className="flex flex-wrap items-center gap-2 text-sm border-b border-stone-100 pb-2">
                <span className="font-mono text-xs text-stone-400">{new Date(h.occurred_at).toLocaleString()}</span>
                <span>{h.from_status} → <strong>{h.to_status}</strong></span>
                {h.changed_by_email ? <span className="text-stone-500">by {h.changed_by_email}</span> : null}
                {h.reason ? <span className="text-stone-500">— {h.reason}</span> : null}
              </li>
            ))
          )}
        </ul>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Notifications sent</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {(app.notifications ?? []).length === 0 ? (
            <li className="text-stone-500">No notifications yet.</li>
          ) : (
            app.notifications!.map((n) => (
              <li key={n.id} className="flex justify-between border-b border-stone-100 pb-2">
                <span>{n.channel} · {n.event_type}</span>
                <span className={n.status === "SENT" ? "text-green-700" : "text-red-600"}>{n.status}</span>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
