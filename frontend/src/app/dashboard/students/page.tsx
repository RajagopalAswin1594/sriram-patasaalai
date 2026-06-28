"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/components/AuthProvider";
import { fetchBatches } from "@/lib/academics";
import type { Batch } from "@/lib/academics";
import {
  bulkAssignBatch,
  createStudent,
  fetchParentLinks,
  fetchStudentEnrollments,
  linkParentChild,
} from "@/lib/students";
import type { ParentChildLink, StudentEnrollment } from "@/lib/students";
import { apiFetch } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";

export default function StudentsPage() {
  const { hasPermission } = useAuth();
  const [enrollments, setEnrollments] = useState<StudentEnrollment[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [parents, setParents] = useState<User[]>([]);
  const [links, setLinks] = useState<ParentChildLink[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [batchId, setBatchId] = useState("");
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "Student@123456",
    first_name: "",
    admission_number: "",
    batch_id: "",
  });
  const [linkForm, setLinkForm] = useState({ parent_id: "", student_id: "", relationship_type: "GUARDIAN" });

  const load = async () => {
    const [e, b, l] = await Promise.all([fetchStudentEnrollments(), fetchBatches(), fetchParentLinks()]);
    setEnrollments(e);
    setBatches(b);
    setLinks(l);
    if (b[0] && !batchId) setBatchId(b[0].id);
    const users = await apiFetch<Paginated<User>>("/users/?user_type=PARENT");
    setParents(users.results.filter((u) => u.user_type === "PARENT"));
  };

  useEffect(() => {
    load().catch(() => setError("Failed to load students"));
  }, []);

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const onBulkAssign = async () => {
    if (!batchId || selected.size === 0) return;
    await bulkAssignBatch(batchId, Array.from(selected));
    setSelected(new Set());
    await load();
  };

  const onCreateStudent = async (e: FormEvent) => {
    e.preventDefault();
    const branchId = batches.find((b) => b.id === form.batch_id)?.branch ?? batches[0]?.branch;
    await createStudent({
      email: form.email,
      password: form.password,
      branch_id: branchId,
      batch_id: form.batch_id || undefined,
      profile: { first_name: form.first_name, last_name: "" },
      type_profile: { admission_number: form.admission_number },
    });
    setShowCreate(false);
    await load();
  };

  const onLinkParent = async (e: FormEvent) => {
    e.preventDefault();
    await linkParentChild(linkForm);
    setLinkForm({ parent_id: "", student_id: "", relationship_type: "GUARDIAN" });
    await load();
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <PageHeader title="Students" description="Active student profiles, batch enrollment, and parent linking." />
        {hasPermission("students.add") ? (
          <button type="button" onClick={() => setShowCreate((v) => !v)} className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">
            {showCreate ? "Cancel" : "Create student"}
          </button>
        ) : null}
      </div>

      {error ? <p className="text-red-600">{error}</p> : null}

      {showCreate ? (
        <form onSubmit={onCreateStudent} className="grid gap-3 rounded-xl border bg-white p-4 md:grid-cols-2">
          <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="Admission number" value={form.admission_number} onChange={(e) => setForm({ ...form, admission_number: e.target.value })} className="rounded-lg border px-3 py-2" />
          <select value={form.batch_id} onChange={(e) => setForm({ ...form, batch_id: e.target.value })} className="rounded-lg border px-3 py-2 md:col-span-2">
            <option value="">Select batch (optional)</option>
            {batches.map((b) => (
              <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
            ))}
          </select>
          <button type="submit" className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white md:col-span-2">Create active student</button>
        </form>
      ) : null}

      {hasPermission("students.change") ? (
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Bulk batch assignment</h2>
          <p className="mt-1 text-sm text-stone-500">Select students and assign to a batch. Mid-year transfers close the prior enrollment record.</p>
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <select value={batchId} onChange={(e) => setBatchId(e.target.value)} className="rounded-lg border px-3 py-2 text-sm">
              {batches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
            <button type="button" onClick={onBulkAssign} disabled={selected.size === 0} className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
              Assign {selected.size} student(s)
            </button>
          </div>
        </section>
      ) : null}

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Enrolled students</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b text-left text-stone-500">
                {hasPermission("students.change") ? <th className="py-2 pr-4">Select</th> : null}
                <th className="py-2 pr-4">Student</th>
                <th className="py-2 pr-4">Branch</th>
                <th className="py-2 pr-4">Current batch</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {enrollments.map((row) => (
                <tr key={row.id} className="border-b border-stone-100">
                  {hasPermission("students.change") ? (
                    <td className="py-2 pr-4">
                      <input type="checkbox" checked={selected.has(row.student)} onChange={() => toggle(row.student)} />
                    </td>
                  ) : null}
                  <td className="py-2 pr-4">
                    <p className="font-medium">{row.student_name}</p>
                    <p className="text-xs text-stone-500">{row.student_email}</p>
                  </td>
                  <td className="py-2 pr-4">{row.branch_code}</td>
                  <td className="py-2 pr-4">{row.current_batch ? `${row.current_batch.name} (${row.current_batch.code})` : "—"}</td>
                  <td className="py-2">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {hasPermission("students.change") ? (
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Parent–child linking</h2>
          <form onSubmit={onLinkParent} className="mt-4 grid gap-3 md:grid-cols-3">
            <select value={linkForm.parent_id} onChange={(e) => setLinkForm({ ...linkForm, parent_id: e.target.value })} className="rounded-lg border px-3 py-2" required>
              <option value="">Select parent</option>
              {parents.map((p) => (
                <option key={p.id} value={p.id}>{p.profile?.display_name || p.email}</option>
              ))}
            </select>
            <select value={linkForm.student_id} onChange={(e) => setLinkForm({ ...linkForm, student_id: e.target.value })} className="rounded-lg border px-3 py-2" required>
              <option value="">Select student</option>
              {enrollments.map((e) => (
                <option key={e.student} value={e.student}>{e.student_name}</option>
              ))}
            </select>
            <button type="submit" className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-semibold text-white">Link accounts</button>
          </form>
          <ul className="mt-4 space-y-2 text-sm">
            {links.map((link) => (
              <li key={link.id} className="flex justify-between border-b border-stone-100 pb-2">
                <span>{link.parent_email} → {link.student_name}</span>
                <span className="text-stone-500">{link.relationship_type}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
