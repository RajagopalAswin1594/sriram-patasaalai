"use client";

import { useEffect, useState } from "react";

import { fetchDocumentView, reviewDocument } from "@/lib/admissions";
import type { NotifyChannel } from "@/lib/admissions";

export type DocumentItem = {
  id: string;
  document_type: string;
  file_name: string;
  content_type: string;
  upload_status: string;
  review_notes?: string;
  reviewed_at?: string;
  reviewed_by_email?: string;
};

const DOC_LABELS: Record<string, string> = {
  STUDENT_PHOTO: "Student Photo",
  BIRTH_CERTIFICATE: "Birth Certificate",
  PREVIOUS_SCHOOL_RECORD: "School Record",
  AADHAAR: "Aadhaar",
  OTHER: "Other Document",
};

const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-stone-200 text-stone-600",
  UPLOADED: "bg-amber-100 text-amber-800",
  VERIFIED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  RESUBMIT_REQUESTED: "bg-orange-100 text-orange-800",
};

const PREVIEWABLE = new Set(["UPLOADED", "VERIFIED", "REJECTED", "RESUBMIT_REQUESTED"]);

type ReviewAction = "APPROVE" | "REJECT" | "REQUEST_RESUBMIT";

export function DocumentPreview({
  applicationId,
  document,
  canReview = false,
  onReviewed,
}: {
  applicationId: string;
  document: DocumentItem;
  canReview?: boolean;
  onReviewed?: () => void;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [pendingAction, setPendingAction] = useState<ReviewAction | null>(null);
  const [reason, setReason] = useState("");
  const [channels, setChannels] = useState<NotifyChannel[]>(["EMAIL", "SMS", "WHATSAPP"]);
  const [reviewError, setReviewError] = useState("");

  const label = DOC_LABELS[document.document_type] ?? document.document_type;
  const canPreview = PREVIEWABLE.has(document.upload_status);
  const isImage = document.content_type?.startsWith("image/");
  const isPdf = document.content_type === "application/pdf";
  const awaitingReview = document.upload_status === "UPLOADED";

  useEffect(() => {
    if (!canPreview) return;

    let active = true;
    let url: string | null = null;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const blob = await fetchDocumentView(applicationId, document.id);
        url = URL.createObjectURL(blob);
        if (active) setObjectUrl(url);
      } catch {
        if (active) setError("Unable to load document preview.");
      } finally {
        if (active) setLoading(false);
      }
    };

    load();

    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [applicationId, document.id, canPreview]);

  const toggleChannel = (channel: NotifyChannel) => {
    setChannels((prev) =>
      prev.includes(channel) ? prev.filter((c) => c !== channel) : [...prev, channel],
    );
  };

  const openReviewForm = (action: ReviewAction) => {
    setPendingAction(action);
    setReason("");
    setReviewError("");
    setShowForm(true);
  };

  const submitReview = async () => {
    if (!pendingAction) return;
    if (pendingAction !== "APPROVE" && !reason.trim()) {
      setReviewError("Please provide a reason for the applicant.");
      return;
    }
    if (channels.length === 0) {
      setReviewError("Select at least one notification channel.");
      return;
    }

    setReviewing(true);
    setReviewError("");
    try {
      await reviewDocument(applicationId, document.id, pendingAction, reason.trim(), channels);
      setShowForm(false);
      setPendingAction(null);
      onReviewed?.();
    } catch {
      setReviewError("Failed to submit document review.");
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="font-semibold text-stone-900">{label}</p>
          <p className="text-xs text-stone-500">{document.file_name}</p>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[document.upload_status] ?? "bg-stone-200 text-stone-600"}`}>
          {document.upload_status.replace(/_/g, " ")}
        </span>
      </div>

      {!canPreview ? (
        <p className="text-sm text-stone-500">Document not uploaded yet.</p>
      ) : loading ? (
        <p className="text-sm text-stone-500">Loading preview...</p>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : objectUrl && isImage ? (
        <div className="overflow-hidden rounded-lg border border-stone-200 bg-white">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={objectUrl} alt={label} className="mx-auto max-h-[28rem] w-full object-contain" />
        </div>
      ) : objectUrl && isPdf ? (
        <div className="overflow-hidden rounded-lg border border-stone-200 bg-white">
          <iframe src={objectUrl} title={label} className="h-[28rem] w-full" />
        </div>
      ) : objectUrl ? (
        <p className="text-sm text-stone-500">Preview is not available for this file type.</p>
      ) : null}

      {document.review_notes ? (
        <p className="mt-3 text-sm text-stone-600">
          <span className="font-medium">Review note:</span> {document.review_notes}
          {document.reviewed_by_email ? (
            <span className="block text-xs text-stone-400">
              by {document.reviewed_by_email}
              {document.reviewed_at ? ` · ${new Date(document.reviewed_at).toLocaleString()}` : ""}
            </span>
          ) : null}
        </p>
      ) : null}

      {canReview && awaitingReview ? (
        <div className="mt-4 border-t border-stone-200 pt-4">
          {!showForm ? (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => openReviewForm("APPROVE")}
                className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700"
              >
                Approve
              </button>
              <button
                type="button"
                onClick={() => openReviewForm("REJECT")}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
              >
                Reject
              </button>
              <button
                type="button"
                onClick={() => openReviewForm("REQUEST_RESUBMIT")}
                className="rounded-lg bg-orange-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-orange-700"
              >
                Request resubmit
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm font-medium text-stone-800">
                {pendingAction === "APPROVE" ? "Approve document" : pendingAction === "REJECT" ? "Reject document" : "Request resubmission"}
              </p>
              {pendingAction !== "APPROVE" ? (
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Reason sent to applicant..."
                  className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm"
                  rows={3}
                />
              ) : null}
              <div>
                <p className="mb-1 text-xs font-medium text-stone-600">Notify via</p>
                <div className="flex flex-wrap gap-3 text-sm">
                  {(["EMAIL", "SMS", "WHATSAPP"] as NotifyChannel[]).map((channel) => (
                    <label key={channel} className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={channels.includes(channel)}
                        onChange={() => toggleChannel(channel)}
                      />
                      {channel === "EMAIL" ? "Email" : channel === "SMS" ? "SMS" : "WhatsApp"}
                    </label>
                  ))}
                </div>
              </div>
              {reviewError ? <p className="text-sm text-red-600">{reviewError}</p> : null}
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={reviewing}
                  onClick={submitReview}
                  className="rounded-lg bg-saffron-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {reviewing ? "Sending..." : "Confirm & notify"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs font-medium text-stone-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
