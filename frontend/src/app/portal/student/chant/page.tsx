"use client";

import { useEffect, useRef, useState } from "react";

import { evaluateChant, fetchChantEvaluations, type ChantEvaluation } from "@/lib/chant";

const DEFAULT_REFERENCE = "oṃ namo bhagavate vāsudevāya";

export default function ChantEvaluatorPage() {
  const [reference, setReference] = useState(DEFAULT_REFERENCE);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<ChantEvaluation | null>(null);
  const [history, setHistory] = useState<ChantEvaluation[]>([]);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  useEffect(() => {
    fetchChantEvaluations().then(setHistory).catch(() => setHistory([]));
  }, [result]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunks.current = [];
    recorder.ondataavailable = (e) => chunks.current.push(e.data);
    recorder.onstop = async () => {
      const blob = new Blob(chunks.current, { type: "audio/webm" });
      stream.getTracks().forEach((t) => t.stop());
      setStatus("Analyzing pronunciation...");
      try {
        const evaluation = await evaluateChant(reference, blob);
        setResult(evaluation);
        setStatus("Evaluation complete.");
      } catch (err) {
        setStatus(err instanceof Error ? err.message : "Evaluation failed");
      }
    };
    mediaRecorder.current = recorder;
    recorder.start();
    setRecording(true);
    setStatus("Recording — chant the reference text clearly.");
    setResult(null);
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setRecording(false);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">AI Chant Evaluator</h1>
        <p className="text-stone-500">Record your chant and receive phonetic feedback syllable by syllable.</p>
      </div>

      <section className="rounded-xl border bg-white p-5">
        <label className="block text-sm font-medium">Reference text (IAST / transliteration)</label>
        <textarea
          rows={2}
          className="mt-2 w-full rounded-lg border px-3 py-2 text-sm"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
        />
        <div className="mt-6 text-center">
          {!recording ? (
            <button type="button" onClick={startRecording} className="rounded-full bg-red-600 px-8 py-4 text-lg font-semibold text-white">
              Record & evaluate
            </button>
          ) : (
            <button type="button" onClick={stopRecording} className="rounded-full bg-stone-800 px-8 py-4 text-lg font-semibold text-white">
              Stop
            </button>
          )}
          {status ? <p className="mt-4 text-sm text-stone-600">{status}</p> : null}
        </div>
      </section>

      {result ? (
        <section className="rounded-xl border bg-white p-5">
          <div className="flex items-baseline justify-between">
            <h2 className="font-semibold">Results</h2>
            <span className="text-3xl font-bold text-saffron-700">{result.phonetic_score}%</span>
          </div>
          <p className="mt-2 text-sm text-stone-600">{result.feedback}</p>
          <p className="mt-1 text-xs text-stone-400">Mode: {result.evaluation_mode} · Heard: “{result.transcribed_text}”</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {result.syllable_scores.map((s) => (
              <span
                key={s.index}
                className={`rounded px-2 py-1 text-xs ${
                  s.score >= 80 ? "bg-green-100 text-green-800" : s.score >= 60 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                }`}
                title={`Expected: ${s.expected} · Spoken: ${s.spoken}`}
              >
                {s.expected || "?"} {s.score}%
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {history.length > 0 ? (
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">Recent evaluations</h2>
          <ul className="mt-3 text-sm">
            {history.slice(0, 5).map((h) => (
              <li key={h.id} className="border-b py-2 flex justify-between">
                <span className="truncate">{h.reference_text.slice(0, 40)}...</span>
                <span className="font-medium">{h.phonetic_score}%</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
