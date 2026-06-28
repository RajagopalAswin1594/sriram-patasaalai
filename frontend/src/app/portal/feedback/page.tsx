"use client";

import { PageHeader } from "@/components/PageHeader";
import { GurukulamFeedbackSubmitForm } from "@/components/GurukulamFeedbackSubmitForm";

export default function PortalGurukulamFeedbackPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Gurukulam feedback"
        description="Share suggestions, concerns, or appreciation about Gurukulam. Reviewed by the administration team."
      />
      <GurukulamFeedbackSubmitForm />
    </div>
  );
}
