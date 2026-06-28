"use client";

import { useEffect, useRef, useState } from "react";

type MediaPlayerProps = {
  url: string;
  contentType: string;
  title?: string;
};

const AUDIO_SPEEDS = [0.75, 1, 1.25, 1.5, 2];

export function MediaPlayer({ url, contentType, title }: MediaPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [speed, setSpeed] = useState(1);

  const isVideo = contentType.startsWith("video/");
  const isAudio = contentType.startsWith("audio/");

  useEffect(() => {
    const el = isVideo ? videoRef.current : audioRef.current;
    if (el) el.playbackRate = speed;
  }, [speed, isVideo, url]);

  if (!url) return <p className="text-sm text-stone-500">Media unavailable.</p>;

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      {title ? <p className="mb-2 font-medium text-stone-900">{title}</p> : null}
      {isVideo ? (
        <video ref={videoRef} src={url} controls preload="metadata" className="w-full rounded-lg" playsInline />
      ) : isAudio ? (
        <div className="space-y-3">
          <audio ref={audioRef} src={url} controls preload="metadata" className="w-full" />
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-stone-500">Speed:</span>
            {AUDIO_SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSpeed(s)}
                className={`rounded px-2 py-1 ${speed === s ? "bg-saffron-600 text-white" : "bg-stone-100 text-stone-700"}`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      ) : (
        <iframe src={url} title={title ?? "Document"} className="h-[32rem] w-full rounded-lg border" />
      )}
    </div>
  );
}
