"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/components/AuthProvider";
import { apiFetch } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";

export default function UsersPage() {
  const { hasPermission } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    user_type: "STUDENT",
    first_name: "",
  });
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Paginated<User>>("/users/");
      setUsers(data.results);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => setError("Failed to load users"));
  }, []);

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await apiFetch("/users/", {
        method: "POST",
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          user_type: form.user_type,
          profile: { first_name: form.first_name, last_name: "" },
        }),
      });
      setShowForm(false);
      setForm({ email: "", password: "", user_type: "STUDENT", first_name: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <PageHeader title="Users" description="Manage students, acharyas, admins, and other personas." />
        {hasPermission("users.add") ? (
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white"
          >
            {showForm ? "Cancel" : "Add user"}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <form onSubmit={onCreate} className="mb-6 grid gap-3 rounded-xl border border-stone-200 bg-white p-4 md:grid-cols-2">
          <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <input placeholder="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="rounded-lg border px-3 py-2" required />
          <select value={form.user_type} onChange={(e) => setForm({ ...form, user_type: e.target.value })} className="rounded-lg border px-3 py-2">
            {["STUDENT", "PARENT", "ACHARYA", "BRANCH_ADMIN", "DONOR", "HOSTEL_WARDEN"].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button type="submit" className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-semibold text-white md:col-span-2">Create user</button>
        </form>
      ) : null}

      {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-4 py-6 text-stone-500" colSpan={4}>Loading...</td></tr>
            ) : users.map((user) => (
              <tr key={user.id} className="border-t border-stone-100">
                <td className="px-4 py-3">{user.email}</td>
                <td className="px-4 py-3">{user.profile?.display_name || user.profile?.first_name}</td>
                <td className="px-4 py-3">{user.user_type}</td>
                <td className="px-4 py-3">{user.account_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
