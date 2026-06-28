"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";

export default function CommunityPortalLayout({ children }: { children: React.ReactNode }) {
  const { me, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !me) router.replace("/login");
    const allowed = ["STUDENT", "ALUMNI", "ACHARYA", "PARENT"];
    if (!loading && me && !me.is_super_admin && !allowed.includes(me.user.user_type)) {
      router.replace("/dashboard");
    }
  }, [loading, me, router]);

  if (loading || !me) return <div className="flex min-h-screen items-center justify-center text-stone-500">Loading...</div>;

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="flex items-center justify-between border-b bg-white px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700">Community Portal</p>
          <p className="text-sm text-stone-600">{me.user.profile?.display_name || me.user.email}</p>
        </div>
        <button type="button" onClick={() => logout()} className="rounded-lg border px-3 py-2 text-sm">Sign out</button>
      </header>
      <main className="mx-auto max-w-5xl p-6">{children}</main>
    </div>
  );
}
