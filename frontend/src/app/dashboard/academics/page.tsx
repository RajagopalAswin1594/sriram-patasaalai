"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { fetchBatches, fetchCourses, fetchShakhas } from "@/lib/academics";
import type { Batch, Shakha, VedicCourse } from "@/lib/academics";

export default function AcademicsPage() {
  const [shakhas, setShakhas] = useState<Shakha[]>([]);
  const [courses, setCourses] = useState<VedicCourse[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);

  useEffect(() => {
    Promise.all([fetchShakhas(), fetchCourses(), fetchBatches()]).then(([s, c, b]) => {
      setShakhas(s);
      setCourses(c);
      setBatches(b);
    });
  }, []);

  return (
    <div className="space-y-8">
      <PageHeader title="Academics" description="Vedic shakhas, courses, and batches (many-to-many course assignment per batch)." />

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Shakhas</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {shakhas.map((s) => (
            <div key={s.id} className="rounded-lg border border-stone-200 p-3">
              <p className="font-medium">{s.name}</p>
              <p className="text-xs text-stone-500">{s.code}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Vedic courses</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {courses.map((c) => (
            <li key={c.id} className="flex justify-between border-b border-stone-100 pb-2">
              <span>{c.name} · {c.grade_level}</span>
              <span className="text-stone-500">{c.shakha_name}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Batches</h2>
        <div className="mt-3 grid gap-4 lg:grid-cols-2">
          {batches.map((b) => (
            <div key={b.id} className="rounded-lg border border-stone-200 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold">{b.name}</p>
                  <p className="text-xs text-stone-500">{b.code} · {b.branch_name} · {b.academic_year_name}</p>
                </div>
                <span className="text-xs text-stone-500">{b.enrolled_count}/{b.capacity}</span>
              </div>
              <p className="mt-2 text-sm text-stone-600">
                Courses: {b.courses?.map((c) => c.name).join(", ") || "—"}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
