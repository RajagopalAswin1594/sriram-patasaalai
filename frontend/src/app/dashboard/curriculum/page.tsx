"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { fetchCourses } from "@/lib/academics";
import { createLesson, createModule, createSyllabus, fetchSyllabi, publishSyllabus } from "@/lib/curriculum";
import type { Syllabus } from "@/lib/curriculum";

export default function CurriculumPage() {
  const [courses, setCourses] = useState<Array<{ id: string; name: string; code: string }>>([]);
  const [syllabi, setSyllabi] = useState<Syllabus[]>([]);
  const [courseId, setCourseId] = useState("");
  const [syllabusId, setSyllabusId] = useState("");
  const [moduleTitle, setModuleTitle] = useState("");
  const [moduleTitleSa, setModuleTitleSa] = useState("");
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonText, setLessonText] = useState("");

  const load = async () => {
    const c = await fetchCourses();
    setCourses(c);
    if (c[0] && !courseId) setCourseId(c[0].id);
    const s = await fetchSyllabi(courseId || c[0]?.id);
    setSyllabi(s);
    if (s[0]) setSyllabusId(s[0].id);
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, [courseId]);

  const onCreateSyllabus = async () => {
    await createSyllabus({ course_id: courseId, version_label: `v${(syllabi.length || 0) + 1}.0` });
    await load();
  };

  const onAddModule = async (e: FormEvent) => {
    e.preventDefault();
    await createModule({ syllabus: syllabusId, title: moduleTitle, title_sa: moduleTitleSa, sort_order: 1 });
    setModuleTitle("");
    await load();
  };

  const onAddLesson = async (e: FormEvent) => {
    e.preventDefault();
    const syllabus = syllabi.find((s) => s.id === syllabusId);
    const moduleId = syllabus?.modules?.[0]?.id;
    if (!moduleId) return;
    await createLesson({ module: moduleId, title: lessonTitle, content_text: lessonText, sort_order: 1 });
    setLessonTitle("");
    setLessonText("");
    await load();
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Curriculum" description="Course modules, lessons, Unicode content, and syllabus versioning." />
      <div className="flex flex-wrap gap-3">
        <select value={courseId} onChange={(e) => setCourseId(e.target.value)} className="rounded-lg border px-3 py-2 text-sm">
          {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button type="button" onClick={onCreateSyllabus} className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">New syllabus version</button>
        {syllabusId ? (
          <button type="button" onClick={() => publishSyllabus(syllabusId).then(load)} className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white">Publish draft</button>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={onAddModule} className="space-y-3 rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Add module</h2>
          <input placeholder="Module title" value={moduleTitle} onChange={(e) => setModuleTitle(e.target.value)} className="w-full rounded-lg border px-3 py-2" required />
          <input placeholder="Sanskrit title (Unicode)" value={moduleTitleSa} onChange={(e) => setModuleTitleSa(e.target.value)} className="w-full rounded-lg border px-3 py-2" />
          <button type="submit" className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-semibold text-white">Add module</button>
        </form>
        <form onSubmit={onAddLesson} className="space-y-3 rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Add lesson</h2>
          <input placeholder="Lesson title" value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} className="w-full rounded-lg border px-3 py-2" required />
          <textarea placeholder="Lesson text (Sanskrit/Tamil Unicode supported)" value={lessonText} onChange={(e) => setLessonText(e.target.value)} className="w-full rounded-lg border px-3 py-2" rows={4} />
          <button type="submit" className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-semibold text-white">Add lesson</button>
        </form>
      </div>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Syllabus tree</h2>
        <div className="mt-4 space-y-4">
          {syllabi.map((s) => (
            <div key={s.id} className="rounded-lg border border-stone-200 p-4">
              <p className="font-medium">{s.version_label} · {s.status}</p>
              {s.modules?.map((m) => (
                <div key={m.id} className="mt-3 ml-4 border-l-2 border-saffron-200 pl-3">
                  <p className="font-medium">{m.title} {m.title_sa ? <span className="text-stone-600">({m.title_sa})</span> : null}</p>
                  <ul className="mt-2 space-y-2 text-sm text-stone-600">
                    {m.lessons?.map((l) => (
                      <li key={l.id}>
                        <span className="font-medium text-stone-800">{l.title}</span>
                        {l.content_text ? <p className="mt-1 whitespace-pre-wrap font-serif">{l.content_text}</p> : null}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
