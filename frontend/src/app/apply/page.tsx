"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  confirmDocument,
  confirmPayment,
  createApplication,
  fetchApplyBranches,
  initiatePayment,
  presignDocument,
  submitApplication,
  type Application,
  type ApplyBranch,
  uploadDocumentFile,
} from "@/lib/admissions";
import { ApiError } from "@/lib/api";

const STEPS = [
  { id: 1, title: "Branch", hint: "பாடசாலை தேர்வு" },
  { id: 2, title: "Student", hint: "மாணவர் விவரம்" },
  { id: 3, title: "Family", hint: "குடும்ப விவரம்" },
  { id: 4, title: "Documents", hint: "ஆவணங்கள்" },
  { id: 5, title: "Payment", hint: "கட்டணம்" },
  { id: 6, title: "Done", hint: "முடிந்தது" },
];

const DOC_TYPES = [
  { type: "STUDENT_PHOTO", label: "Student Photo", hint: "மாணவர் புகைப்படம்", required: true },
  { type: "BIRTH_CERTIFICATE", label: "Birth Certificate", hint: "பிறப்பு சான்றிதழ்", required: true },
  { type: "PREVIOUS_SCHOOL_RECORD", label: "School Record", hint: "பள்ளி ஆவணம்", required: false },
  { type: "AADHAAR", label: "Aadhaar", hint: "ஆதார்", required: false },
];

const GRADES = ["Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shastri Entry"];

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-base font-semibold text-stone-800">{label}</span>
      {hint ? <span className="mb-2 block text-sm text-stone-500">{hint}</span> : null}
      {children}
    </label>
  );
}

const inputClass =
  "w-full rounded-xl border-2 border-stone-200 px-4 py-3 text-lg text-stone-900 focus:border-saffron-500";

export default function ApplyPage() {
  const [step, setStep] = useState(1);
  const [branches, setBranches] = useState<ApplyBranch[]>([]);
  const [application, setApplication] = useState<Application | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  const [form, setForm] = useState({
    branch_id: "",
    student_first_name: "",
    student_last_name: "",
    date_of_birth: "",
    gender: "",
    grade_applying: GRADES[0],
    previous_school: "",
    parent_name: "",
    parent_phone: "",
    parent_email: "",
    relationship: "GUARDIAN",
    address_line_1: "",
    address_line_2: "",
    city: "",
    state: "Tamil Nadu",
    postal_code: "",
    preferred_language: "ta",
    data_consent: false,
  });

  useEffect(() => {
    fetchApplyBranches().then(setBranches).catch(() => setError("Could not load branches. Please try again."));
  }, []);

  const startApplication = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const app = await createApplication(form);
      setApplication(app);
      setStep(4);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start application");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (documentType: string, file: File) => {
    if (!application) return;
    setError("");
    try {
      const { document_id, upload } = await presignDocument(application.id, application.access_token, documentType, file);
      await uploadDocumentFile(upload, file, (pct) => setUploadProgress((p) => ({ ...p, [documentType]: pct })));
      await confirmDocument(application.id, application.access_token, document_id);
      setUploadProgress((p) => ({ ...p, [documentType]: 100 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  const handleSubmitAndPay = async () => {
    if (!application) return;
    setError("");
    setLoading(true);
    try {
      const submitted = await submitApplication(application.id, application.access_token);
      setApplication(submitted);
      setStep(5);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Please upload all required documents");
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!application) return;
    setError("");
    setLoading(true);
    try {
      const payment = await initiatePayment(application.id, application.access_token);
      if (payment.demo_mode) {
        const completed = await confirmPayment(application.id, application.access_token);
        setApplication(completed);
        setStep(6);
        return;
      }
      // Razorpay integration when keys are configured
      const completed = await confirmPayment(application.id, application.access_token, {
        order_id: payment.order_id,
        payment_id: `rzp_${payment.order_id}`,
        signature: "production_requires_razorpay_checkout",
      });
      setApplication(completed);
      setStep(6);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Payment failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-saffron-50 to-white">
      <header className="border-b border-stone-200 bg-white px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700">Digital Veda Gurukulam</p>
            <h1 className="text-xl font-bold text-stone-900">Online Admission Application</h1>
            <p className="text-sm text-stone-500">ஆன்லைன் சேர்க்கை விண்ணப்பம்</p>
          </div>
          <Link href="/login" className="text-sm font-medium text-saffron-700 hover:underline">
            Staff login
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        <ol className="mb-8 flex flex-wrap gap-2">
          {STEPS.map((s) => (
            <li
              key={s.id}
              className={`rounded-full px-3 py-1 text-sm font-medium ${
                step === s.id ? "bg-saffron-600 text-white" : step > s.id ? "bg-saffron-100 text-saffron-800" : "bg-stone-100 text-stone-500"
              }`}
            >
              {s.title}
            </li>
          ))}
        </ol>

        {error ? (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div>
        ) : null}

        {step === 1 ? (
          <form onSubmit={startApplication} className="space-y-5 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-2xl font-bold text-stone-900">Choose your Patasala</h2>
              <p className="mt-1 text-stone-500">உங்கள் பாடசாலையைத் தேர்ந்தெடுக்கவும்</p>
            </div>
            <Field label="Branch / பாடசாலை">
              <select
                required
                className={inputClass}
                value={form.branch_id}
                onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
              >
                <option value="">Select a branch...</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.code}) — {b.city}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Student first name / மாணவர் பெயர்" hint="As per birth certificate">
              <input required className={inputClass} value={form.student_first_name} onChange={(e) => setForm({ ...form, student_first_name: e.target.value })} />
            </Field>
            <Field label="Date of birth / பிறந்த தேதி">
              <input required type="date" className={inputClass} value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
            </Field>
            <Field label="Grade applying for / வகுப்பு">
              <select className={inputClass} value={form.grade_applying} onChange={(e) => setForm({ ...form, grade_applying: e.target.value })}>
                {GRADES.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </Field>
            <Field label="Parent / Guardian name / பெற்றோர் பெயர்">
              <input required className={inputClass} value={form.parent_name} onChange={(e) => setForm({ ...form, parent_name: e.target.value })} />
            </Field>
            <Field label="Mobile number / கைபேசி எண்" hint="We will send updates to this number">
              <input required type="tel" className={inputClass} value={form.parent_phone} onChange={(e) => setForm({ ...form, parent_phone: e.target.value })} />
            </Field>
            <Field label="Address / முகவரி">
              <input required className={inputClass} value={form.address_line_1} onChange={(e) => setForm({ ...form, address_line_1: e.target.value })} />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="City / நகரம்">
                <input required className={inputClass} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
              </Field>
              <Field label="PIN code">
                <input required className={inputClass} value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} />
              </Field>
            </div>
            <label className="flex items-start gap-3 rounded-xl border border-stone-200 bg-stone-50 p-4">
              <input
                type="checkbox"
                required
                checked={form.data_consent}
                onChange={(e) => setForm({ ...form, data_consent: e.target.checked })}
                className="mt-1 h-5 w-5"
              />
              <span className="text-sm text-stone-700">
                I consent to the collection and processing of personal data for admission purposes.
                <span className="block text-stone-500">தனிப்பட்ட தரவு சேகரிப்புக்கு நான் ஒப்புக்கொள்கிறேன்.</span>
              </span>
            </label>
            <button type="submit" disabled={loading} className="w-full rounded-xl bg-saffron-600 py-4 text-lg font-bold text-white hover:bg-saffron-700 disabled:opacity-60">
              {loading ? "Please wait..." : "Continue →"}
            </button>
          </form>
        ) : null}

        {step === 4 && application ? (
          <div className="space-y-5 rounded-2xl border bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold">Upload documents</h2>
            <p className="text-stone-500">PDF, JPG or PNG. Max 10 MB each. Files upload directly — no server delay.</p>
            {DOC_TYPES.map((doc) => (
              <div key={doc.type} className="rounded-xl border-2 border-dashed border-stone-200 p-4">
                <p className="text-lg font-semibold">{doc.label} {doc.required ? "*" : ""}</p>
                <p className="text-sm text-stone-500">{doc.hint}</p>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  className="mt-3 block w-full text-base"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleUpload(doc.type, file);
                  }}
                />
                {uploadProgress[doc.type] !== undefined ? (
                  <div className="mt-2 h-3 overflow-hidden rounded-full bg-stone-100">
                    <div className="h-full bg-saffron-500 transition-all" style={{ width: `${uploadProgress[doc.type]}%` }} />
                  </div>
                ) : null}
              </div>
            ))}
            <button type="button" onClick={handleSubmitAndPay} disabled={loading} className="w-full rounded-xl bg-saffron-600 py-4 text-lg font-bold text-white">
              Review & pay fee →
            </button>
          </div>
        ) : null}

        {step === 5 && application ? (
          <div className="space-y-5 rounded-2xl border bg-white p-6 shadow-sm text-center">
            <h2 className="text-2xl font-bold">Application fee</h2>
            <p className="text-4xl font-bold text-saffron-700">₹{application.application_fee_amount}</p>
            <p className="text-stone-500">Application #{application.application_number}</p>
            <button type="button" onClick={handlePayment} disabled={loading} className="w-full rounded-xl bg-saffron-600 py-4 text-lg font-bold text-white">
              {loading ? "Processing..." : "Pay application fee"}
            </button>
            <p className="text-xs text-stone-400">Demo mode when payment gateway is not configured</p>
          </div>
        ) : null}

        {step === 6 && application ? (
          <div className="rounded-2xl border border-green-200 bg-green-50 p-8 text-center">
            <div className="text-5xl">✓</div>
            <h2 className="mt-4 text-2xl font-bold text-green-900">Application submitted!</h2>
            <p className="mt-2 text-green-800">விண்ணப்பம் வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது</p>
            <p className="mt-4 text-lg font-semibold">Reference: {application.application_number}</p>
            <p className="mt-2 text-stone-600">Save this number. We will contact you at {form.parent_phone}.</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
