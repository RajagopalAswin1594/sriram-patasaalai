"use client";

import { FormEvent, useState } from "react";

import { searchCurriculum } from "@/lib/learning";

export default function StudentSearchPage() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Awaited<ReturnType<typeof searchCurriculum>> | null>(null);

  const onSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (q.length < 2) return;
    const data = await searchCurriculum(q);
    setResults(data);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Learning library search</h1>
      <form onSubmit={onSearch} className="flex gap-2">
        <input
          className="flex-1 rounded-lg border px-3 py-2 text-sm"
          placeholder="Search lessons, Sanskrit text, resources..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button type="submit" className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">Search</button>
      </form>
      {results ? (
        <div className="grid gap-6 md:grid-cols-2">
          <section className="rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Lessons</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {results.lessons.map((l) => (
                <li key={l.id} className="border-b pb-2">
                  <p className="font-medium">{l.title}</p>
                  <p className="text-xs text-stone-500">{l.course} · {l.module}</p>
                </li>
              ))}
            </ul>
          </section>
          <section className="rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Resources</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {results.resources.map((r) => (
                <li key={r.id} className="border-b pb-2">
                  <p className="font-medium">{r.title}</p>
                  <p className="text-xs text-stone-500">{r.resource_type} · {r.lesson_title}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}
    </div>
  );
}
