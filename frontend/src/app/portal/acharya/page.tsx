"use client";

import { useEffect, useState } from "react";

import { fetchAcharyaPortal } from "@/lib/scheduling";
import type { AcharyaPortalData } from "@/lib/scheduling";

export default function AcharyaCalendarPage() {
  const [data, setData] = useState<AcharyaPortalData | null>(null);

  useEffect(() => {
    const from = new Date();
    const to = new Date();
    to.setDate(to.getDate() + 30);
    fetchAcharyaPortal(from.toISOString(), to.toISOString()).then(setData).catch(() => setData(null));
  }, []);

  if (!data) return <p className="text-stone-500">Loading calendar...</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My teaching calendar</h1>
        <p className="text-stone-500">Assigned branches, shakha specializations, and upcoming sessions.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Branches</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.branches.map((b, i) => (
              <li key={i} className="flex justify-between border-b border-stone-100 pb-2">
                <span>{b.branch_name}</span>
                <span className="text-stone-500">{b.branch_timezone}{b.is_primary ? " · primary" : ""}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Shakha specialization</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.shakhas.map((s, i) => (
              <li key={i} className="flex justify-between border-b border-stone-100 pb-2">
                <span>{s.shakha_name}</span>
                <span className="text-stone-500">{s.shakha_code}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Upcoming sessions (30 days)</h2>
        <ul className="mt-4 space-y-3">
          {data.sessions.length === 0 ? (
            <li className="text-sm text-stone-500">No sessions in this period.</li>
          ) : (
            data.sessions.map((s) => (
              <li key={s.id} className="rounded-lg border border-stone-200 p-4 text-sm">
                <p className="font-semibold">{s.title}</p>
                <p className="text-stone-600">{s.batch_name} · {s.branch_code}</p>
                <p className="text-xs text-stone-500">
                  {new Date(s.starts_at).toLocaleString(undefined, { timeZone: s.timezone })} ({s.timezone})
                </p>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
