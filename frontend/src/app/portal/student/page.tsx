"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { fetchStudentProgress } from "@/lib/learning";

export default function StudentDashboardPage() {
  const [progress, setProgress] = useState<Awaited<ReturnType<typeof fetchStudentProgress>> | null>(null);

  useEffect(() => {
    fetchStudentProgress().then(setProgress).catch(() => setProgress(null));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Student dashboard</h1>
        <p className="text-stone-500">Your academic progress at a glance.</p>
      </div>

      {progress ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Practice submissions</p>
            <p className="text-2xl font-bold">{progress.practice_submissions}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Attendance rate</p>
            <p className="text-2xl font-bold">{progress.attendance.rate}%</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Certificates</p>
            <p className="text-2xl font-bold">{progress.certificates_issued}</p>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <p className="text-xs text-stone-500">Recent exams</p>
            <p className="text-2xl font-bold">{progress.exam_scores.length}</p>
          </div>
        </div>
      ) : (
        <p className="text-stone-500">Loading progress...</p>
      )}

      <div className="flex flex-wrap gap-3">
        <Link href="/portal/student/lessons" className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">Lessons</Link>
        <Link href="/portal/student/practice" className="rounded-lg border px-4 py-2 text-sm font-medium">Practice</Link>
        <Link href="/portal/student/chant" className="rounded-lg border px-4 py-2 text-sm font-medium">Chant AI</Link>
        <Link href="/portal/student/search" className="rounded-lg border px-4 py-2 text-sm font-medium">Search library</Link>
        <Link href="/portal/community" className="rounded-lg border px-4 py-2 text-sm font-medium">Community</Link>
      </div>
    </div>
  );
}
