"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  confirmDonation,
  fetchDonationCategories,
  initiateDonation,
  type Donation,
  type DonationCategory,
} from "@/lib/donations";
import { openRazorpayCheckout, type RazorpayPaymentData } from "@/lib/razorpay";

export default function DonatePage() {
  const [categories, setCategories] = useState<DonationCategory[]>([]);
  const [form, setForm] = useState({
    category_code: "",
    amount: "",
    donor_name: "",
    donor_email: "",
    donor_phone: "",
    pan_number: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState<Donation | null>(null);

  useEffect(() => {
    fetchDonationCategories()
      .then((cats) => {
        setCategories(cats);
        if (cats[0]) setForm((f) => ({ ...f, category_code: cats[0].code, amount: cats[0].min_amount }));
      })
      .catch(() => setError("Unable to load donation categories."));
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { donation, payment } = await initiateDonation(form);
      const pay = payment as RazorpayPaymentData;
      if (pay.demo_mode || pay.gateway === "DEMO") {
        const confirmed = await confirmDonation(donation.id);
        setCompleted(confirmed);
      } else {
        const opened = await openRazorpayCheckout(pay, {
          name: "Digital Veda Gurukulam",
          description: "Donation",
          onSuccess: async (paymentId, signature) => {
            const confirmed = await confirmDonation(donation.id, {
              payment_id: paymentId,
              signature,
              order_id: pay.order_id,
            });
            setCompleted(confirmed);
            setLoading(false);
          },
        });
        if (!opened) setLoading(false);
        return;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Donation failed");
    } finally {
      setLoading(false);
    }
  };

  if (completed) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16">
        <h1 className="text-2xl font-bold text-saffron-800">Thank you for your donation</h1>
        <p className="mt-4 text-stone-600">
          Receipt <strong>{completed.receipt?.receipt_number}</strong> has been generated for ₹{completed.amount}.
        </p>
        {completed.receipt?.download_url ? (
          <a
            href={completed.receipt.download_url}
            className="mt-6 inline-block rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Download tax receipt (12A / 80G)
          </a>
        ) : null}
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-6 py-16">
      <h1 className="text-3xl font-bold text-stone-900">Support Annadanam &amp; Students</h1>
      <p className="mt-2 text-stone-600">Make a tax-deductible donation and receive an immediate 80G receipt.</p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4 rounded-xl border bg-white p-6 shadow-sm">
        <label className="block text-sm">
          <span className="font-medium">Category</span>
          <select
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={form.category_code}
            onChange={(e) => {
              const cat = categories.find((c) => c.code === e.target.value);
              setForm((f) => ({
                ...f,
                category_code: e.target.value,
                amount: cat?.min_amount ?? f.amount,
              }));
            }}
          >
            {categories.map((c) => (
              <option key={c.id} value={c.code}>
                {c.name} (min ₹{c.min_amount})
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium">Amount (₹)</span>
          <input
            type="number"
            required
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={form.amount}
            onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Your name</span>
          <input
            required
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={form.donor_name}
            onChange={(e) => setForm((f) => ({ ...f, donor_name: e.target.value }))}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Email (for receipt)</span>
          <input
            type="email"
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={form.donor_email}
            onChange={(e) => setForm((f) => ({ ...f, donor_email: e.target.value }))}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Phone</span>
          <input
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={form.donor_phone}
            onChange={(e) => setForm((f) => ({ ...f, donor_phone: e.target.value }))}
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">PAN (optional, for 80G)</span>
          <input
            className="mt-1 w-full rounded-lg border px-3 py-2 uppercase"
            maxLength={10}
            value={form.pan_number}
            onChange={(e) => setForm((f) => ({ ...f, pan_number: e.target.value.toUpperCase() }))}
          />
        </label>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-saffron-600 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
        >
          {loading ? "Processing…" : "Donate now"}
        </button>
      </form>
    </main>
  );
}
