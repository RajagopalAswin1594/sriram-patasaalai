"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { portalPathForUserType } from "@/lib/portal";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login, me, loading } = useAuth();
  const [email, setEmail] = useState("admin@gurukulam.local");
  const [password, setPassword] = useState("Admin@Gurukulam1");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && me) {
    window.location.href = portalPathForUserType(me.user.user_type);
    return null;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-saffron-50 via-white to-stone-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700">Digital Veda Gurukulam</p>
          <h1 className="mt-2 text-2xl font-semibold text-stone-900">Foundation Platform</h1>
          <p className="mt-1 text-sm text-stone-500">Sprint 1 – Sign in to continue</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-stone-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-stone-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2"
              required
            />
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-saffron-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-saffron-700 disabled:opacity-60"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-stone-500">
          Applying for admission?{" "}
          <Link href="/apply" className="font-semibold text-saffron-700 hover:underline">
            Start online application
          </Link>
        </p>
      </div>
    </div>
  );
}
