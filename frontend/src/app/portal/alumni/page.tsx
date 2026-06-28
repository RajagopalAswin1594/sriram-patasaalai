"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { fetchAlumniDirectory, fetchAlumniMe, type AlumniProfile } from "@/lib/alumni";

export default function AlumniPortalPage() {
  const [me, setMe] = useState<AlumniProfile | null>(null);
  const [directory, setDirectory] = useState<AlumniProfile[]>([]);

  useEffect(() => {
    Promise.all([fetchAlumniMe(), fetchAlumniDirectory()]).then(([m, d]) => {
      setMe(m);
      setDirectory(d);
    }).catch(() => undefined);
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Alumni portal</h1>
        <p className="text-stone-500">Your profile and the Gurukulam alumni directory.</p>
      </div>

      {me ? (
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">My profile</h2>
          <p className="mt-2 text-sm">{me.display_name} · Class of {me.graduation_year}</p>
          <p className="text-sm text-stone-600">{me.current_city} · {me.current_occupation}</p>
          <Link href="/portal/community" className="mt-3 inline-block text-sm text-saffron-700 hover:underline">
            Community events →
          </Link>
          <Link href="/donate" className="ml-4 inline-block text-sm text-saffron-700 hover:underline">
            Alumni giving →
          </Link>
        </section>
      ) : null}

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Alumni directory</h2>
        <ul className="mt-4 divide-y text-sm">
          {directory.length === 0 ? (
            <li className="py-3 text-stone-500">No alumni listed yet.</li>
          ) : (
            directory.map((a) => (
              <li key={a.id} className="py-3">
                <p className="font-medium">{a.display_name}</p>
                <p className="text-stone-500">{a.graduation_year} · {a.batch_name} · {a.current_city}</p>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
