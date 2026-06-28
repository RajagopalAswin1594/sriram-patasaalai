"use client";

import Link from "next/link";

import { GurukulamFeedbackSubmitForm } from "@/components/GurukulamFeedbackSubmitForm";

export default function PublicGurukulamFeedbackPage() {
  return (
    <main className="min-h-screen bg-stone-50 py-12">
      <div className="mx-auto max-w-3xl px-6">
        <Link href="/" className="text-sm text-saffron-700 hover:underline">← Home</Link>
        <h1 className="mt-4 text-2xl font-bold text-stone-900">Gurukulam feedback</h1>
        <p className="mt-2 text-stone-600">
          Share feedback about teaching, facilities, events, or your overall experience at Gurukulam.
          For application bugs, Super Admins use the internal development feedback channel.
        </p>
        <div className="mt-8">
          <GurukulamFeedbackSubmitForm />
        </div>
      </div>
    </main>
  );
}
