"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { fetchBatches, fetchCourses } from "@/lib/academics";
import { fetchStudentEnrollments } from "@/lib/students";
import {
  createExam,
  fetchAttendanceAlerts,
  issueCertificate,
  markAttendance,
  reviewPractice,
  upsertExamScore,
} from "@/lib/learning";
import { fetchPracticeSubmissions } from "@/lib/learning";

export default function LearningPage() {
  const [batches, setBatches] = useState<Array<{ id: string; name: string; branch: string }>>([]);
  const [students, setStudents] = useState<Array<{ student: string; student_name: string }>>([]);
  const [batchId, setBatchId] = useState("");
  const [attendance, setAttendance] = useState<Record<string, string>>({});
  const [alerts, setAlerts] = useState<Array<{ student_id: string; attendance_rate: number }>>([]);
  const [pendingPractice, setPendingPractice] = useState<Array<{ id: string; student_email: string; title: string }>>([]);
  const [courses, setCourses] = useState<Array<{ id: string; code: string }>>([]);

  useEffect(() => {
    Promise.all([fetchBatches(), fetchStudentEnrollments(), fetchCourses(), fetchPracticeSubmissions("SUBMITTED")]).then(
      ([b, e, c, p]) => {
        setBatches(b);
        setStudents(e.map((x) => ({ student: x.student, student_name: x.student_name })));
        setCourses(c);
        setPendingPractice(p as Array<{ id: string; student_email: string; title: string }>);
        if (b[0]) setBatchId(b[0].id);
      },
    );
  }, []);

  const onMarkAttendance = async (e: FormEvent) => {
    e.preventDefault();
    await markAttendance({
      batch_id: batchId,
      session_date: new Date().toISOString().slice(0, 10),
      records: students.map((s) => ({
        student_id: s.student,
        status: attendance[s.student] ?? "PRESENT",
      })),
    });
    const a = await fetchAttendanceAlerts(batchId);
    setAlerts(a as Array<{ student_id: string; attendance_rate: number }>);
  };

  const onScheduleExam = async () => {
    if (!batchId || !courses[0]) return;
    await createExam({
      batch: batchId,
      course: courses[0].id,
      title: "Oral Pariksha",
      exam_type: "ORAL",
      scheduled_at: new Date().toISOString(),
      max_score: 100,
    });
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Learning" description="Attendance, practice review, exams, and certificates." />

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Daily attendance grid</h2>
        <form onSubmit={onMarkAttendance} className="mt-4 space-y-3">
          <select value={batchId} onChange={(e) => setBatchId(e.target.value)} className="rounded-lg border px-3 py-2 text-sm">
            {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <div className="grid gap-2 sm:grid-cols-2">
            {students.map((s) => (
              <label key={s.student} className="flex items-center justify-between rounded border px-3 py-2 text-sm">
                <span>{s.student_name}</span>
                <select
                  value={attendance[s.student] ?? "PRESENT"}
                  onChange={(e) => setAttendance({ ...attendance, [s.student]: e.target.value })}
                  className="rounded border px-2 py-1"
                >
                  {["PRESENT", "ABSENT", "LATE", "EXCUSED"].map((st) => <option key={st} value={st}>{st}</option>)}
                </select>
              </label>
            ))}
          </div>
          <button type="submit" className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">Save attendance</button>
        </form>
        {alerts.length > 0 ? (
          <div className="mt-4 rounded-lg bg-orange-50 p-3 text-sm text-orange-800">
            Low attendance alerts: {alerts.map((a) => `${a.student_id} (${Math.round(a.attendance_rate * 100)}%)`).join(", ")}
          </div>
        ) : null}
      </section>

      <section className="rounded-xl border bg-white p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Practice submissions (pending review)</h2>
        </div>
        <ul className="mt-3 space-y-2 text-sm">
          {pendingPractice.map((p) => (
            <li key={p.id} className="flex items-center justify-between border-b border-stone-100 pb-2">
              <span>{p.student_email} · {p.title}</span>
              <button
                type="button"
                onClick={() => reviewPractice(p.id, "Good pronunciation. Continue daily practice.", "Madhyamam")}
                className="rounded bg-green-600 px-2 py-1 text-xs font-semibold text-white"
              >
                Approve
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Exams & certificates</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" onClick={onScheduleExam} className="rounded-lg border px-4 py-2 text-sm">Schedule oral exam</button>
          {students[0] && batchId && courses[0] ? (
            <button
              type="button"
              onClick={() =>
                upsertExamScore({
                  exam_id: "00000000-0000-0000-0000-000000000001",
                  student_id: students[0].student,
                  score: 85,
                  oral_grade: "Madhyamam",
                }).catch(() => undefined)
              }
              className="rounded-lg border px-4 py-2 text-sm"
            >
              Sample score entry
            </button>
          ) : null}
          {students[0] && batchId && courses[0] ? (
            <button
              type="button"
              onClick={() => issueCertificate({ student_id: students[0].student, course_id: courses[0].id, batch_id: batchId })}
              className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Issue certificate
            </button>
          ) : null}
        </div>
      </section>
    </div>
  );
}
