"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { createHostelRoom, fetchHostels, fetchOccupancyMap, type OccupancyHostel } from "@/lib/hostel";

export default function HostelDashboardPage() {
  const [hostels, setHostels] = useState<{ id: string; name: string; code: string }[]>([]);
  const [selectedHostel, setSelectedHostel] = useState("");
  const [occupancy, setOccupancy] = useState<OccupancyHostel[]>([]);
  const [roomForm, setRoomForm] = useState({ room_number: "", floor: "1", capacity: 2 });
  const [error, setError] = useState("");

  const load = async () => {
    const h = await fetchHostels();
    setHostels(h);
    const hostelId = selectedHostel || h[0]?.id;
    if (hostelId && !selectedHostel) setSelectedHostel(hostelId);
    const map = await fetchOccupancyMap(hostelId);
    setOccupancy(map);
  };

  useEffect(() => {
    load().catch(() => setError("Failed to load hostel data"));
  }, [selectedHostel]);

  const onAddRoom = async () => {
    if (!selectedHostel || !roomForm.room_number) return;
    await createHostelRoom({ hostel_id: selectedHostel, ...roomForm });
    setRoomForm({ room_number: "", floor: "1", capacity: 2 });
    await load();
  };

  const hostel = occupancy[0];

  return (
    <div className="space-y-8">
      <PageHeader title="Hostel management" description="Room mapping, occupancy, and branch-scoped hostel data." />

      <div className="flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="font-medium">Hostel</span>
          <select
            className="ml-2 rounded-lg border px-3 py-2"
            value={selectedHostel}
            onChange={(e) => setSelectedHostel(e.target.value)}
          >
            {hostels.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.code})
              </option>
            ))}
          </select>
        </label>
        <div className="flex gap-2 text-sm">
          <input
            placeholder="Room #"
            className="rounded-lg border px-2 py-1"
            value={roomForm.room_number}
            onChange={(e) => setRoomForm((f) => ({ ...f, room_number: e.target.value }))}
          />
          <input
            placeholder="Floor"
            className="w-16 rounded-lg border px-2 py-1"
            value={roomForm.floor}
            onChange={(e) => setRoomForm((f) => ({ ...f, floor: e.target.value }))}
          />
          <button type="button" onClick={onAddRoom} className="rounded-lg bg-saffron-600 px-3 py-1 text-white">
            Add room
          </button>
        </div>
      </div>

      {error ? <p className="text-red-600">{error}</p> : null}

      {hostel ? (
        <section className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold">{hostel.name} — room map</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {hostel.rooms.map((room) => (
              <div
                key={room.id}
                className={`rounded-lg border p-4 text-sm ${
                  room.status === "OCCUPIED" ? "border-amber-300 bg-amber-50" : "border-stone-200"
                }`}
              >
                <p className="font-semibold">
                  {room.room_number} <span className="text-stone-500">· Floor {room.floor}</span>
                </p>
                <p className="text-xs text-stone-500">
                  {room.occupants.length}/{room.capacity} · {room.status}
                </p>
                <ul className="mt-2 space-y-1">
                  {room.occupants.map((o) => (
                    <li key={o.assignment_id} className="text-xs">
                      {o.student_name}{" "}
                      <span className={o.leave_status === "ON_LEAVE" ? "text-orange-600" : "text-green-700"}>
                        ({o.leave_status.replace("_", " ")})
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <p className="text-stone-500">No hostel data. Run seed_epic5.</p>
      )}
    </div>
  );
}
