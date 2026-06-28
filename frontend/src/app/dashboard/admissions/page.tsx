"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/components/AuthProvider";
import {
  fetchAdminApplicationStats,
  fetchAdminApplications,
  reviewApplication,
} from "@/lib/admissions";
import type { Application } from "@/lib/admissions";
import { ApiError } from "@/lib/api";

const STATUS_TABS = [
  { key: "", label: "All" },
  { key: "PENDING", label: "Pending" },
  { key: "APPROVED", label: "Approved" },
  { key: "REJECTED", label: "Rejected" },
];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: "bg-amber-100 text-amber-900",
    UNDER_REVIEW: "bg-amber-100 text-amber-900",
    APPROVED: "bg-green-100 text-green-900",
    REJECTED: "bg-red-100 text-red-900",
    DRAFT: "bg-stone-100 text-stone-700",
    PAYMENT_PENDING: "bg-blue-100 text-blue-900",
  };
  const label = status === "UNDER_REVIEW" ? "PENDING" : status;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors[status] ?? "bg-stone-100"}`}>
      {label}
    </span>
  );
}

export default function AdmissionsAdminPage() {
  const { hasPermission } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState({ pending: 0, approved: 0, rejected: 0, stale_pending: 0, total: 0 });
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reviewing, setReviewing] = useState<Application | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [data, statsData] = await Promise.all([
        fetchAdminApplications(filter || undefined),
        fetchAdminApplicationStats(),
      ]);
      setApplications(data.results);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hasPermission("admissions.view")) load();
  }, [hasPermission, filter]);

  const handleReview = async (status: "APPROVED" | "REJECTED") => {
    if (!reviewing) return;
    try {
      await reviewApplication(reviewing.id, status, rejectionReason, reviewNotes);
      setReviewing(null);
      setRejectionReason("");
      setReviewNotes("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review failed");
    }
  };

  if (!hasPermission("admissions.view")) {
    return <p className="text-stone-500">You do not have permission to view admissions.</p>;
  }

  return (
    <div>
      <PageHeader
        title="Application Review"
        description="Review pending applications, approve or reject, and track notification delivery."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          { label: "Pending", value: stats.pending, color: "text-amber-700" },
          { label: "Approved", value: stats.approved, color: "text-green-700" },
          { label: "Rejected", value: stats.rejected, color: "text-red-700" },
          { label: "Stale (>7d)", value: stats.stale_pending, color: "text-orange-700" },
          { label: "Total", value: stats.total, color: "text-stone-700" },
        ].map((card) => (
          <div key={card.label} className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-stone-500">{card.label}</p>
            <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setFilter(tab.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              filter === tab.key ? "bg-saffron-600 text-white" : "bg-white border border-stone-200 text-stone-600"
            }`}
          >
            {tab.label}
          </button>
        ))}
        <a href="/apply" target="_blank" rel="noreferrer" className="ml-auto text-sm font-medium text-saffron-700 hover:underline">
          Public apply link ↗
        </a>
      </div>

      {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-hidden rounded-xl border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-500">
            <tr>
              <th className="px-4 py-3">Application #</th>
              <th className="px-4 py-3">Student</th>
              <th className="px-4 py-3">Branch</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Submitted</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-6">Loading...</td></tr>
            ) : applications.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-6 text-stone-500">No applications in this queue.</td></tr>
            ) : applications.map((app) => (
              <tr key={app.id} className="border-t border-stone-100 hover:bg-stone-50">
                <td className="px-4 py-3 font-mono text-xs">
                  <Link href={`/dashboard/admissions/${app.id}`} className="text-saffron-700 hover:underline">
                    {app.application_number}
                  </Link>
                </td>
                <td className="px-4 py-3">{app.student_first_name} {app.student_last_name}</td>
                <td className="px-4 py-3">{app.branch_code}</td>
                <td className="px-4 py-3"><StatusBadge status={app.status} /></td>
                <td className="px-4 py-3 text-stone-500">{app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Link href={`/dashboard/admissions/${app.id}`} className="text-xs font-medium text-saffron-700 hover:underline">
                      View
                    </Link>
                    {(app.status === "PENDING" || app.status === "UNDER_REVIEW") && hasPermission("admissions.approve") ? (
                      <button type="button" onClick={() => setReviewing(app)} className="text-xs font-medium text-green-700">
                        Review
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {reviewing ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold">Review {reviewing.application_number}</h3>
            <p className="mt-1 text-sm text-stone-500">{reviewing.student_first_name} — {reviewing.branch_name}</p>
            <label className="mt-4 block text-sm font-medium">Rejection reason (if rejecting)</label>
            <textarea
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              rows={2}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
            />
            <label className="mt-3 block text-sm font-medium">Internal notes</label>
            <textarea
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              rows={2}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
            />
            <div className="mt-6 flex gap-3">
              <button type="button" onClick={() => handleReview("APPROVED")} className="flex-1 rounded-lg bg-green-600 py-2.5 text-sm font-semibold text-white">
                Approve
              </button>
              <button type="button" onClick={() => handleReview("REJECTED")} className="flex-1 rounded-lg bg-red-600 py-2.5 text-sm font-semibold text-white">
                Reject
              </button>
              <button type="button" onClick={() => setReviewing(null)} className="rounded-lg border px-4 py-2.5 text-sm">
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
