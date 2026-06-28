"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { verifyCertificate } from "@/lib/learning";

export default function VerifyCertificatePage() {
  const params = useParams();
  const code = params.code as string;
  const [result, setResult] = useState<Record<string, string> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!code) return;
    verifyCertificate(code).then((body) => {
      if (body.success) setResult(body.data);
      else setError(body.error?.message ?? "Not found");
    });
  }, [code]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-lg">
        <h1 className="text-xl font-bold">Certificate verification</h1>
        {error ? <p className="mt-4 text-red-600">{error}</p> : null}
        {result ? (
          <dl className="mt-4 space-y-2 text-sm">
            <div><dt className="text-stone-500">Certificate</dt><dd className="font-medium">{result.certificate_number}</dd></div>
            <div><dt className="text-stone-500">Student</dt><dd>{result.student_name}</dd></div>
            <div><dt className="text-stone-500">Course</dt><dd>{result.course_name}</dd></div>
            <div><dt className="text-stone-500">Branch</dt><dd>{result.branch_name}</dd></div>
            <div><dt className="text-stone-500">Issued</dt><dd>{new Date(result.issued_at).toLocaleDateString()}</dd></div>
            <div><dt className="text-stone-500">Status</dt><dd className="font-semibold text-green-700">{result.status}</dd></div>
          </dl>
        ) : null}
      </div>
    </div>
  );
}
