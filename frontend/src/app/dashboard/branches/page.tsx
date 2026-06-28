"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/components/AuthProvider";
import { apiFetch } from "@/lib/api";
import type { Branch, Paginated } from "@/lib/types";

export default function BranchesPage() {
  const { hasPermission } = useAuth();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", city: "" });

  const load = async () => {
    const data = await apiFetch<Paginated<Branch>>("/branches/");
    setBranches(data.results);
    setLoading(false);
  };

  useEffect(() => {
    load().catch(() => setLoading(false));
  }, []);

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    await apiFetch("/branches/", {
      method: "POST",
      body: JSON.stringify({ ...form, status: "ACTIVE", country: "IN" }),
    });
    setShowForm(false);
    setForm({ code: "", name: "", city: "" });
    await load();
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <PageHeader title="Branches" description="Multi-branch Gurukulam centers." />
        {hasPermission("branches.add") ? (
          <button type="button" onClick={() => setShowForm((v) => !v)} className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">
            {showForm ? "Cancel" : "Add branch"}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <form onSubmit={onCreate} className="mb-6 grid gap-3 rounded-xl border bg-white p-4 md:grid-cols-3">
          <input placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="rounded-lg border px-3 py-2" />
          <button type="submit" className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-semibold text-white md:col-span-3">Create branch</button>
        </form>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-500">
            <tr>
              <th className="px-4 py-3">Code</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">HQ</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-4 py-6" colSpan={5}>Loading...</td></tr>
            ) : branches.map((branch) => (
              <tr key={branch.id} className="border-t border-stone-100">
                <td className="px-4 py-3 font-mono text-xs">{branch.code}</td>
                <td className="px-4 py-3">{branch.name}</td>
                <td className="px-4 py-3">{branch.city || "—"}</td>
                <td className="px-4 py-3">{branch.status}</td>
                <td className="px-4 py-3">{branch.is_headquarters ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
