"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { FeedbackSubmitForm } from "@/components/FeedbackSubmitForm";
import { useAuth } from "@/components/AuthProvider";

const PORTAL_HOME: Record<string, string> = {
  STUDENT: "/portal/student",
  PARENT: "/portal/parent",
  ACHARYA: "/portal/acharya",
  DONOR: "/portal/donor",
  ALUMNI: "/portal/alumni",
  HOSTEL_WARDEN: "/portal/warden",
};

export default function PortalFeedbackLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !me) router.replace("/login?next=/portal/feedback");
  }, [loading, me, router]);

  if (loading || !me) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">Loading…</div>;
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b bg-white px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700">Gurukulam Feedback</p>
            <nav className="mt-2 flex gap-4 text-sm">
              <Link href="/portal/feedback" className="text-saffron-700 hover:underline">Submit</Link>
              <Link href="/portal/feedback/mine" className="text-saffron-700 hover:underline">My feedback</Link>
            </nav>
          </div>
          <Link
            href={me.is_super_admin ? "/dashboard" : (PORTAL_HOME[me.user.user_type] ?? "/dashboard")}
            className="text-sm text-stone-600 hover:underline"
          >
            ← Back
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl p-6">{children}</main>
    </div>
  );
}
