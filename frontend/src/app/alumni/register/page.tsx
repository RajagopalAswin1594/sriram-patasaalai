"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { registerAlumni } from "@/lib/alumni";
import { login } from "@/lib/api";

export default function AlumniRegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    graduation_year: new Date().getFullYear() - 5,
    batch_name: "",
    current_city: "",
    current_occupation: "",
    bio: "",
  });
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await registerAlumni(form);
      await login(form.email, form.password);
      router.push("/portal/alumni");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  return (
    <main className="mx-auto max-w-lg px-6 py-16">
      <Link href="/" className="text-sm text-saffron-700 hover:underline">← Home</Link>
      <h1 className="mt-4 text-2xl font-bold">Alumni registration</h1>
      <p className="mt-2 text-stone-600">Join the alumni directory and community events.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-3">
        <input required type="email" placeholder="Email" className="w-full rounded border px-3 py-2 text-sm" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
        <input required type="password" minLength={12} placeholder="Password (12+ chars)" className="w-full rounded border px-3 py-2 text-sm" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
        <input required placeholder="First name" className="w-full rounded border px-3 py-2 text-sm" value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} />
        <input placeholder="Last name" className="w-full rounded border px-3 py-2 text-sm" value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} />
        <input required type="number" placeholder="Graduation year" className="w-full rounded border px-3 py-2 text-sm" value={form.graduation_year} onChange={(e) => setForm((f) => ({ ...f, graduation_year: Number(e.target.value) }))} />
        <input placeholder="Batch / course" className="w-full rounded border px-3 py-2 text-sm" value={form.batch_name} onChange={(e) => setForm((f) => ({ ...f, batch_name: e.target.value }))} />
        <input placeholder="Current city" className="w-full rounded border px-3 py-2 text-sm" value={form.current_city} onChange={(e) => setForm((f) => ({ ...f, current_city: e.target.value }))} />
        <textarea placeholder="Bio (optional)" rows={3} className="w-full rounded border px-3 py-2 text-sm" value={form.bio} onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))} />
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button type="submit" className="w-full rounded-lg bg-saffron-600 py-2.5 text-sm font-semibold text-white">Register</button>
      </form>
    </main>
  );
}
