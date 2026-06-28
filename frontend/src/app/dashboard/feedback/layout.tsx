"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { FeedbackSubnav } from "@/components/FeedbackSubnav";
import { useAuth } from "@/components/AuthProvider";

export default function ApplicationFeedbackLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && me && !me.is_super_admin) {
      router.replace("/dashboard/gurukulam-feedback");
    }
  }, [loading, me, router]);

  if (loading || !me || !me.is_super_admin) {
    return <div className="text-sm text-stone-500">Super Admin access required for application development feedback.</div>;
  }

  return (
    <div className="space-y-6">
      <FeedbackSubnav />
      {children}
    </div>
  );
}
