"use client";

import { useEffect, useState } from "react";

import { MediaPlayer } from "@/components/MediaPlayer";
import { fetchResourceStream, fetchSyllabi } from "@/lib/curriculum";
import { fetchCourses } from "@/lib/academics";

export default function StudentLessonsPage() {
  const [resources, setResources] = useState<Array<{ id: string; title: string; content_type: string; url: string }>>([]);

  useEffect(() => {
    (async () => {
      const courses = await fetchCourses();
      if (!courses[0]) return;
      const syllabi = await fetchSyllabi(courses[0].id);
      const published = syllabi.find((s) => s.status === "PUBLISHED") ?? syllabi[0];
      const items: Array<{ id: string; title: string; content_type: string; url: string }> = [];
      for (const mod of published?.modules ?? []) {
        for (const lesson of mod.lessons ?? []) {
          for (const res of lesson.resources ?? []) {
            if (res.stream_url) {
              items.push({ id: res.id, title: res.title, content_type: res.content_type || "application/pdf", url: res.stream_url });
            } else if (res.text_body) {
              items.push({ id: res.id, title: res.title, content_type: "text/plain", url: "" });
            }
          }
        }
      }
      setResources(items);
    })();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Lesson media</h1>
      <p className="text-stone-500">Stream lectures and chants with adjustable audio speed.</p>
      {resources.length === 0 ? (
        <p className="text-sm text-stone-500">No published lesson media yet.</p>
      ) : (
        resources.map((r) => (
          <MediaPlayer key={r.id} url={r.url} contentType={r.content_type} title={r.title} />
        ))
      )}
    </div>
  );
}
