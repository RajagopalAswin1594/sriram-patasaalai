"use client";

import { useEffect, useState } from "react";

import { fetchWardenPortal, updateLeaveStatus } from "@/lib/hostel";

export default function WardenPortalPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchWardenPortal>> | null>(null);

  const load = () => fetchWardenPortal().then(setData).catch(() => setData(null));

  useEffect(() => {
    load();
  }, []);

  const toggleLeave = async (assignmentId: string, current: string) => {
    const next = current === "ON_LEAVE" ? "IN_RESIDENCE" : "ON_LEAVE";
    await updateLeaveStatus(assignmentId, next);
    await load();
  };

  if (!data) return <p className="text-stone-500">Loading warden portal…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Warden portal</h1>
        <p className="text-stone-500">Occupancy, leave status, and mess eligibility by branch.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-white p-4">
          <p className="text-xs text-stone-500">In residence</p>
          <p className="text-2xl font-bold">{data.stats.in_residence}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <p className="text-xs text-stone-500">On leave</p>
          <p className="text-2xl font-bold text-orange-600">{data.stats.on_leave}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <p className="text-xs text-stone-500">Mess eligible today</p>
          <p className="text-2xl font-bold text-green-700">{data.stats.mess_eligible}</p>
        </div>
      </div>

      {data.occupancy.map((hostel) => (
        <section key={hostel.id} className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">{hostel.name}</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {hostel.rooms.map((room) => (
              <div key={room.id} className="rounded-lg border p-3 text-sm">
                <p className="font-medium">Room {room.room_number}</p>
                {room.occupants.map((o) => (
                  <div key={o.assignment_id} className="mt-2 flex items-center justify-between">
                    <span>
                      {o.student_name}
                      <br />
                      <span className="text-xs text-stone-500">
                        Mess: {o.mess_eligible ? "Yes" : "No"}
                      </span>
                    </span>
                    <button
                      type="button"
                      onClick={() => toggleLeave(o.assignment_id, o.leave_status)}
                      className="rounded border px-2 py-1 text-xs hover:bg-stone-50"
                    >
                      {o.leave_status === "ON_LEAVE" ? "Mark in" : "Mark leave"}
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
