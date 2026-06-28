"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { BranchSelector } from "@/components/BranchSelector";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/components/AuthProvider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !me) router.replace("/login");
  }, [loading, me, router]);

  if (loading || !me) {
    return (
      <div className="flex min-h-screen items-center justify-center text-stone-500">Loading...</div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-stone-200 bg-white px-6 py-4">
          <p className="text-sm text-stone-500">Signed in as {me.user.email}</p>
          <BranchSelector />
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
