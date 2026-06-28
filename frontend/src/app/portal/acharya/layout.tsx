"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/components/AuthProvider";

export default function AcharyaPortalLayout({ children }: { children: React.ReactNode }) {
  const { me, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !me) router.replace("/login");
    if (!loading && me && me.user.user_type !== "ACHARYA" && !me.is_super_admin) {
      router.replace("/dashboard");
    }
  }, [loading, me, router]);

  if (loading || !me) return <div className="flex min-h-screen items-center justify-center text-stone-500">Loading...</div>;

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b bg-white px-6 py-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700">Acharya Portal</p>
          <p className="text-sm text-stone-600">{me.user.profile?.display_name || me.user.email}</p>
          <nav className="mt-2 flex gap-4 text-sm">
            <Link href="/portal/acharya" className="text-saffron-700 hover:underline">Dashboard</Link>
            <Link href="/portal/feedback" className="text-saffron-700 hover:underline">Gurukulam Feedback</Link>
          </nav>
        </div>
        <button type="button" onClick={() => logout()} className="rounded-lg border px-3 py-2 text-sm">Sign out</button>
      </header>
      <main className="mx-auto max-w-5xl p-6">{children}</main>
    </div>
  );
}
