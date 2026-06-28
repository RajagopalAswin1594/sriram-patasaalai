"use client";

import { PageHeader } from "@/components/PageHeader";
import { FeedbackSubmitForm } from "@/components/FeedbackSubmitForm";

export default function DashboardFeedbackSubmitPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Application development feedback"
        description="Super Admin only. Report bugs, enhancements, and platform issues. Routed through AI analysis and GitHub/DevOps."
      />
      <FeedbackSubmitForm />
    </div>
  );
}
