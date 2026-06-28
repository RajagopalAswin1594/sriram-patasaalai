"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import type { AuditLog, AuthEvent, Paginated } from "@/lib/types";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [events, setEvents] = useState<AuthEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<Paginated<AuditLog>>("/audit/logs/"),
      apiFetch<Paginated<AuthEvent>>("/audit/auth-events/"),
    ])
      .then(([logData, eventData]) => {
        setLogs(logData.results);
        setEvents(eventData.results);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeader title="Audit" description="Entity changes and authentication events." />

      <section>
        <h3 className="mb-3 font-semibold text-stone-900">Entity audit logs</h3>
        <div className="overflow-hidden rounded-xl border bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-stone-50 text-left text-stone-500">
              <tr>
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Actor</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="px-4 py-6" colSpan={4}>Loading...</td></tr>
              ) : logs.map((log) => (
                <tr key={log.id} className="border-t border-stone-100">
                  <td className="px-4 py-3">{new Date(log.occurred_at).toLocaleString()}</td>
                  <td className="px-4 py-3">{log.action}</td>
                  <td className="px-4 py-3">{log.entity_repr || log.entity_type}</td>
                  <td className="px-4 py-3">{log.actor_email || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="mb-3 font-semibold text-stone-900">Authentication events</h3>
        <div className="overflow-hidden rounded-xl border bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-stone-50 text-left text-stone-500">
              <tr>
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">Event</th>
                <th className="px-4 py-3">Outcome</th>
                <th className="px-4 py-3">User</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="px-4 py-6" colSpan={4}>Loading...</td></tr>
              ) : events.map((event) => (
                <tr key={event.id} className="border-t border-stone-100">
                  <td className="px-4 py-3">{new Date(event.occurred_at).toLocaleString()}</td>
                  <td className="px-4 py-3">{event.event_type}</td>
                  <td className="px-4 py-3">{event.outcome}</td>
                  <td className="px-4 py-3">{event.user_email || event.email_attempted || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
