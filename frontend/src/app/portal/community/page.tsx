"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  createForumThread,
  fetchCommunityEvents,
  fetchForumCategories,
  fetchForumThread,
  fetchForumThreads,
  flagForumThread,
  replyForumThread,
  rsvpEvent,
  type CommunityEvent,
  type ForumCategory,
  type ForumThread,
} from "@/lib/community";

export default function CommunityPortalPage() {
  const [events, setEvents] = useState<CommunityEvent[]>([]);
  const [categories, setCategories] = useState<ForumCategory[]>([]);
  const [threads, setThreads] = useState<ForumThread[]>([]);
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [threadDetail, setThreadDetail] = useState<Awaited<ReturnType<typeof fetchForumThread>> | null>(null);
  const [newThread, setNewThread] = useState({ category_id: "", title: "", body: "" });
  const [reply, setReply] = useState("");
  const [flagReason, setFlagReason] = useState("");

  const load = async () => {
    const [e, c, t] = await Promise.all([fetchCommunityEvents(), fetchForumCategories(), fetchForumThreads()]);
    setEvents(e);
    setCategories(c);
    setThreads(t);
    if (c[0] && !newThread.category_id) setNewThread((f) => ({ ...f, category_id: c[0].id }));
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (selectedThread) fetchForumThread(selectedThread).then(setThreadDetail).catch(() => setThreadDetail(null));
    else setThreadDetail(null);
  }, [selectedThread]);

  const onRsvp = async (id: string) => {
    await rsvpEvent(id);
    await load();
  };

  const onCreateThread = async (e: FormEvent) => {
    e.preventDefault();
    await createForumThread(newThread.category_id, newThread.title, newThread.body);
    setNewThread((f) => ({ ...f, title: "", body: "" }));
    await load();
  };

  const onReply = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedThread) return;
    await replyForumThread(selectedThread, reply);
    setReply("");
    const detail = await fetchForumThread(selectedThread);
    setThreadDetail(detail);
  };

  const onFlag = async () => {
    if (!selectedThread || !flagReason) return;
    await flagForumThread(selectedThread, flagReason);
    setFlagReason("");
    alert("Thank you — moderators will review this content.");
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Community</h1>
        <p className="text-stone-500">Upcoming events and moderated Dharma discussions.</p>
      </div>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Upcoming events</h2>
        <ul className="mt-4 space-y-3">
          {events.length === 0 ? (
            <li className="text-sm text-stone-500">No upcoming events.</li>
          ) : (
            events.map((ev) => (
              <li key={ev.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-4 text-sm">
                <div>
                  <p className="font-semibold">{ev.title}</p>
                  <p className="text-stone-600">{new Date(ev.starts_at).toLocaleString()} · {ev.location}</p>
                  <p className="text-xs text-stone-500">{ev.rsvp_count} going{ev.capacity ? ` / ${ev.capacity}` : ""}</p>
                </div>
                <button
                  type="button"
                  onClick={() => onRsvp(ev.id)}
                  className="rounded-lg bg-saffron-600 px-3 py-1.5 text-xs font-semibold text-white"
                >
                  {ev.user_rsvp === "GOING" ? "RSVP'd" : "RSVP"}
                </button>
              </li>
            ))
          )}
        </ul>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Forum threads</h2>
          <ul className="mt-3 divide-y text-sm">
            {threads.map((t) => (
              <li key={t.id}>
                <button type="button" onClick={() => setSelectedThread(t.id)} className="w-full py-3 text-left hover:bg-stone-50">
                  <p className="font-medium">{t.title}</p>
                  <p className="text-xs text-stone-500">{t.category_name} · {t.author_name} · {t.post_count} replies</p>
                </button>
              </li>
            ))}
          </ul>
          <form onSubmit={onCreateThread} className="mt-4 space-y-2 border-t pt-4">
            <p className="text-xs font-semibold uppercase text-stone-500">Start a discussion</p>
            <select
              className="w-full rounded border px-2 py-1 text-sm"
              value={newThread.category_id}
              onChange={(e) => setNewThread((f) => ({ ...f, category_id: e.target.value }))}
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <input
              placeholder="Title"
              required
              className="w-full rounded border px-2 py-1 text-sm"
              value={newThread.title}
              onChange={(e) => setNewThread((f) => ({ ...f, title: e.target.value }))}
            />
            <textarea
              placeholder="Your question or reflection"
              required
              rows={3}
              className="w-full rounded border px-2 py-1 text-sm"
              value={newThread.body}
              onChange={(e) => setNewThread((f) => ({ ...f, body: e.target.value }))}
            />
            <button type="submit" className="rounded-lg bg-saffron-600 px-3 py-1.5 text-sm font-semibold text-white">
              Submit for moderation
            </button>
          </form>
        </section>

        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">{threadDetail ? threadDetail.thread.title : "Select a thread"}</h2>
          {threadDetail ? (
            <div className="mt-4 space-y-4 text-sm">
              <p className="whitespace-pre-wrap text-stone-700">{threadDetail.thread.body}</p>
              <ul className="space-y-2 border-t pt-3">
                {threadDetail.posts.map((p) => (
                  <li key={p.id} className="rounded bg-stone-50 p-3">
                    <p className="text-xs font-medium text-stone-500">{p.author_name}</p>
                    <p>{p.body}</p>
                  </li>
                ))}
              </ul>
              <form onSubmit={onReply} className="space-y-2">
                <textarea
                  rows={2}
                  className="w-full rounded border px-2 py-1"
                  placeholder="Reply..."
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                />
                <button type="submit" className="rounded border px-3 py-1 text-xs">Post reply</button>
              </form>
              <div className="flex gap-2 border-t pt-3">
                <input
                  placeholder="Flag reason"
                  className="flex-1 rounded border px-2 py-1 text-xs"
                  value={flagReason}
                  onChange={(e) => setFlagReason(e.target.value)}
                />
                <button type="button" onClick={onFlag} className="rounded border px-2 py-1 text-xs text-red-700">
                  Flag
                </button>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-stone-500">Choose a thread to read and participate.</p>
          )}
        </section>
      </div>
    </div>
  );
}
