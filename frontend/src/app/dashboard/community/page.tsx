"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { fetchModerationQueue, moderatePost, moderateThread, type ForumThread } from "@/lib/community";

export default function CommunityModerationPage() {
  const [queue, setQueue] = useState<Awaited<ReturnType<typeof fetchModerationQueue>> | null>(null);

  const load = () => fetchModerationQueue().then(setQueue).catch(() => setQueue(null));

  useEffect(() => {
    load();
  }, []);

  const approveThread = async (t: ForumThread) => {
    await moderateThread(t.id, "APPROVED");
    await load();
  };

  const rejectThread = async (t: ForumThread) => {
    await moderateThread(t.id, "REJECTED", "Does not meet community guidelines");
    await load();
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Community moderation" description="Review pending threads, posts, and user flags." />

      {!queue ? (
        <p className="text-stone-500">Loading queue...</p>
      ) : (
        <>
          <section className="rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Pending threads ({queue.threads.length})</h2>
            <ul className="mt-4 space-y-3 text-sm">
              {queue.threads.map((t) => (
                <li key={t.id} className="rounded-lg border p-4">
                  <p className="font-semibold">{t.title}</p>
                  <p className="mt-1 text-stone-600">{t.body}</p>
                  <p className="mt-1 text-xs text-stone-500">{t.author_name} · {t.category_name}</p>
                  <div className="mt-3 flex gap-2">
                    <button type="button" onClick={() => approveThread(t)} className="rounded bg-green-700 px-3 py-1 text-xs text-white">
                      Approve
                    </button>
                    <button type="button" onClick={() => rejectThread(t)} className="rounded border px-3 py-1 text-xs text-red-700">
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Pending posts ({queue.posts.length})</h2>
            <ul className="mt-4 space-y-2 text-sm">
              {queue.posts.map((p) => (
                <li key={p.id} className="flex items-center justify-between border-b py-2">
                  <span>{p.author_name}: {p.body.slice(0, 80)}...</span>
                  <button
                    type="button"
                    onClick={() => moderatePost(p.id, "APPROVED").then(load)}
                    className="rounded border px-2 py-1 text-xs"
                  >
                    Approve
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border bg-white p-5">
            <h2 className="font-semibold">Open flags ({queue.flags.length})</h2>
            <ul className="mt-3 text-xs text-stone-600">
              {queue.flags.map((f) => (
                <li key={f.id} className="border-b py-2">{f.reason} ({f.status})</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
