"use client";

import { useEffect, useState } from "react";

import { fetchMyDonations } from "@/lib/learning";
import type { Donation } from "@/lib/donations";

export default function DonorPortalPage() {
  const [donations, setDonations] = useState<Donation[]>([]);

  useEffect(() => {
    fetchMyDonations().then(setDonations).catch(() => setDonations([]));
  }, []);

  const total = donations.reduce((sum, d) => sum + Number(d.amount), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Donor dashboard</h1>
        <p className="text-stone-500">Your completed donations and tax receipts.</p>
      </div>
      <div className="rounded-xl border bg-white p-5">
        <p className="text-sm text-stone-500">Total contributed</p>
        <p className="text-3xl font-bold text-saffron-700">₹{total.toLocaleString()}</p>
      </div>
      <ul className="divide-y rounded-xl border bg-white">
        {donations.length === 0 ? (
          <li className="p-5 text-sm text-stone-500">No donations found for your account email.</li>
        ) : (
          donations.map((d) => (
            <li key={d.id} className="flex items-center justify-between p-5 text-sm">
              <div>
                <p className="font-medium">{d.donation_number}</p>
                <p className="text-stone-500">{d.category?.name ?? "Donation"}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">₹{d.amount}</p>
                {d.receipt?.download_url ? (
                  <a href={d.receipt.download_url} className="text-xs text-saffron-700 hover:underline">Receipt</a>
                ) : null}
              </div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
