"use client";

import { useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/api";
import { fetchBatches } from "@/lib/academics";

export default function StudentPracticePage() {
  const [batchId, setBatchId] = useState("");
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState("");
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  useEffect(() => {
    fetchBatches().then((b) => {
      if (b[0]) setBatchId(b[0].id);
    });
  }, []);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunks.current = [];
    recorder.ondataavailable = (e) => chunks.current.push(e.data);
    recorder.onstop = async () => {
      const blob = new Blob(chunks.current, { type: "audio/webm" });
      await uploadRecording(blob);
      stream.getTracks().forEach((t) => t.stop());
    };
    mediaRecorder.current = recorder;
    recorder.start();
    setRecording(true);
    setStatus("Recording...");
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setRecording(false);
    setStatus("Uploading...");
  };

  const uploadRecording = async (blob: Blob) => {
    const presign = await apiFetch<{ submission_id: string; upload: { upload_type: string; upload_url: string; fields: Record<string, string> } }>(
      "/learning/practice/presign/",
      {
        method: "POST",
        body: JSON.stringify({
          batch_id: batchId,
          title: "Chant practice",
          file_name: "practice.webm",
          content_type: "audio/webm",
          file_size: blob.size,
        }),
      },
    );
    const formData = new FormData();
    Object.entries(presign.upload.fields).forEach(([k, v]) => formData.append(k, v));
    formData.append("file", blob, "practice.webm");
    await fetch(presign.upload.upload_url, { method: "POST", body: formData });
    setStatus("Submitted for Acharya review.");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Practice recording</h1>
      <p className="text-stone-500">Record your chant and submit for Acharya feedback. Supports mobile browsers (webm/mp4).</p>
      <div className="rounded-xl border bg-white p-6 text-center">
        {!recording ? (
          <button type="button" onClick={startRecording} className="rounded-full bg-red-600 px-8 py-4 text-lg font-semibold text-white">
            Start recording
          </button>
        ) : (
          <button type="button" onClick={stopRecording} className="rounded-full bg-stone-800 px-8 py-4 text-lg font-semibold text-white">
            Stop & submit
          </button>
        )}
        {status ? <p className="mt-4 text-sm text-stone-600">{status}</p> : null}
      </div>
    </div>
  );
}
