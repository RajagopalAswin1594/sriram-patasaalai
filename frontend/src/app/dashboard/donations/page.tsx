"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import type { Donation } from "@/lib/donations";

export default function DonationsDashboardPage() {
  const [donations, setDonations] = useState<Donation[]>([]);

  useEffect(() => {
    apiFetch<{ results?: Donation[] } | Donation[]>("/donations/")
      .then((res) => setDonations(Array.isArray(res) ? res : res.results ?? []))
      .catch(() => setDonations([]));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader title="Donations" description="Branch-scoped donation ledger and receipts." />
      <div className="overflow-x-auto rounded-xl border bg-white">
        <table className="w-full text-sm">
          <thead className="border-b bg-stone-50 text-left text-xs uppercase text-stone-500">
            <tr>
              <th className="p-3">Number</th>
              <th className="p-3">Donor</th>
              <th className="p-3">Category</th>
              <th className="p-3">Amount</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {donations.map((d) => (
              <tr key={d.id} className="border-b">
                <td className="p-3">{d.donation_number}</td>
                <td className="p-3">{d.donor_name}</td>
                <td className="p-3">{d.category?.name}</td>
                <td className="p-3">₹{d.amount}</td>
                <td className="p-3">{d.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
