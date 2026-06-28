"use client";

import { useEffect, useState } from "react";

import { fetchMyChildren } from "@/lib/students";
import type { StudentEnrollment } from "@/lib/students";

export default function ParentPortalPage() {
  const [children, setChildren] = useState<StudentEnrollment[]>([]);

  useEffect(() => {
    fetchMyChildren().then(setChildren).catch(() => setChildren([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My children</h1>
        <p className="text-stone-500">You only see students linked to your parent account.</p>
      </div>
      <section className="rounded-xl border bg-white p-5">
        {children.length === 0 ? (
          <p className="text-sm text-stone-500">No linked children found. Contact the branch admin.</p>
        ) : (
          <ul className="space-y-3">
            {children.map((child) => (
              <li key={child.id} className="rounded-lg border border-stone-200 p-4">
                <p className="font-semibold">{child.student_name}</p>
                <p className="text-sm text-stone-600">{child.branch_code} · {child.status}</p>
                <p className="text-sm text-stone-500">
                  Batch: {child.current_batch ? `${child.current_batch.name} (${child.current_batch.code})` : "Not assigned"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
