"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/components/AuthProvider";
import { fetchBatches, fetchShakhas } from "@/lib/academics";
import type { Batch } from "@/lib/academics";
import { createSession, fetchSessions, registerAcharya } from "@/lib/scheduling";
import type { TeachingSession } from "@/lib/scheduling";
import { apiFetch } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";

export default function SchedulingPage() {
  const { hasPermission } = useAuth();
  const [sessions, setSessions] = useState<TeachingSession[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [acharyas, setAcharyas] = useState<User[]>([]);
  const [shakhas, setShakhas] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState("");
  const [sessionForm, setSessionForm] = useState({
    acharya_id: "",
    batch_id: "",
    branch_id: "",
    title: "",
    starts_at: "",
    ends_at: "",
    timezone: "Asia/Kolkata",
    location: "",
  });
  const [acharyaForm, setAcharyaForm] = useState({
    email: "",
    password: "Acharya@123456",
    first_name: "",
    employee_code: "",
    branch_id: "",
    shakha_id: "",
  });

  const load = async () => {
    const [s, b, sh] = await Promise.all([fetchSessions(), fetchBatches(), fetchShakhas()]);
    setSessions(s);
    setBatches(b);
    setShakhas(sh);
    const users = await apiFetch<Paginated<User>>("/users/?user_type=ACHARYA");
    setAcharyas(users.results.filter((u) => u.user_type === "ACHARYA"));
    if (b[0]) {
      setSessionForm((f) => ({ ...f, batch_id: b[0].id, branch_id: b[0].branch }));
      setAcharyaForm((f) => ({ ...f, branch_id: b[0].branch }));
    }
    if (sh[0]) setAcharyaForm((f) => ({ ...f, shakha_id: sh[0].id }));
  };

  useEffect(() => {
    load().catch(() => setError("Failed to load scheduling data"));
  }, []);

  const onCreateSession = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await createSession({
        ...sessionForm,
        starts_at: new Date(sessionForm.starts_at).toISOString(),
        ends_at: new Date(sessionForm.ends_at).toISOString(),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scheduling conflict or validation error");
    }
  };

  const onRegisterAcharya = async (e: FormEvent) => {
    e.preventDefault();
    await registerAcharya({
      email: acharyaForm.email,
      password: acharyaForm.password,
      branch_ids: [acharyaForm.branch_id],
      shakha_ids: [acharyaForm.shakha_id],
      profile: { first_name: acharyaForm.first_name, last_name: "" },
      type_profile: { employee_code: acharyaForm.employee_code, specialization: shakhas.find((s) => s.id === acharyaForm.shakha_id)?.name ?? "" },
    });
    await load();
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Scheduling" description="Acharya mapping, teaching calendar, and conflict-safe session booking." />
      {error ? <p className="text-red-600">{error}</p> : null}

      {hasPermission("scheduling.add") ? (
        <section className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={onRegisterAcharya} className="space-y-3 rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Register Acharya</h2>
            <input placeholder="Email" value={acharyaForm.email} onChange={(e) => setAcharyaForm({ ...acharyaForm, email: e.target.value })} className="w-full rounded-lg border px-3 py-2" required />
            <input placeholder="First name" value={acharyaForm.first_name} onChange={(e) => setAcharyaForm({ ...acharyaForm, first_name: e.target.value })} className="w-full rounded-lg border px-3 py-2" required />
            <input placeholder="Employee code" value={acharyaForm.employee_code} onChange={(e) => setAcharyaForm({ ...acharyaForm, employee_code: e.target.value })} className="w-full rounded-lg border px-3 py-2" />
            <select value={acharyaForm.shakha_id} onChange={(e) => setAcharyaForm({ ...acharyaForm, shakha_id: e.target.value })} className="w-full rounded-lg border px-3 py-2">
              {shakhas.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <button type="submit" className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">Register Acharya</button>
          </form>

          <form onSubmit={onCreateSession} className="space-y-3 rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Schedule session</h2>
            <select value={sessionForm.acharya_id} onChange={(e) => setSessionForm({ ...sessionForm, acharya_id: e.target.value })} className="w-full rounded-lg border px-3 py-2" required>
              <option value="">Select Acharya</option>
              {acharyas.map((a) => <option key={a.id} value={a.id}>{a.profile?.first_name || a.email}</option>)}
            </select>
            <select
              value={sessionForm.batch_id}
              onChange={(e) => {
                const batch = batches.find((b) => b.id === e.target.value);
                setSessionForm({ ...sessionForm, batch_id: e.target.value, branch_id: batch?.branch ?? "" });
              }}
              className="w-full rounded-lg border px-3 py-2"
              required
            >
              {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <input placeholder="Title" value={sessionForm.title} onChange={(e) => setSessionForm({ ...sessionForm, title: e.target.value })} className="w-full rounded-lg border px-3 py-2" required />
            <input type="datetime-local" value={sessionForm.starts_at} onChange={(e) => setSessionForm({ ...sessionForm, starts_at: e.target.value })} className="w-full rounded-lg border px-3 py-2" required />
            <input type="datetime-local" value={sessionForm.ends_at} onChange={(e) => setSessionForm({ ...sessionForm, ends_at: e.target.value })} className="w-full rounded-lg border px-3 py-2" required />
            <input placeholder="Timezone (IANA)" value={sessionForm.timezone} onChange={(e) => setSessionForm({ ...sessionForm, timezone: e.target.value })} className="w-full rounded-lg border px-3 py-2" />
            <button type="submit" className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white">Create session</button>
          </form>
        </section>
      ) : null}

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Teaching calendar</h2>
        <ul className="mt-4 space-y-3">
          {sessions.length === 0 ? (
            <li className="text-sm text-stone-500">No sessions scheduled.</li>
          ) : (
            sessions.map((s) => (
              <li key={s.id} className="rounded-lg border border-stone-200 p-4 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{s.title}</p>
                  <span className="text-xs text-stone-500">{s.status}</span>
                </div>
                <p className="mt-1 text-stone-600">{s.batch_name} · {s.acharya_email}</p>
                <p className="text-xs text-stone-500">
                  {new Date(s.starts_at).toLocaleString()} – {new Date(s.ends_at).toLocaleString()} ({s.timezone})
                </p>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
