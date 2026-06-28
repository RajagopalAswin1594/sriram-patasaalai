"use client";

import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import {
  fetchNotificationLogs,
  fetchNotificationTemplates,
  saveNotificationTemplate,
  testSendNotification,
  type NotificationLog,
  type NotificationTemplate,
} from "@/lib/notifications";

export default function NotificationsPage() {
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [logs, setLogs] = useState<NotificationLog[]>([]);
  const [form, setForm] = useState({
    code: "",
    name: "",
    channel: "EMAIL",
    subject_template: "",
    body_template: "",
  });
  const [testEmail, setTestEmail] = useState("");

  const load = async () => {
    const [t, l] = await Promise.all([fetchNotificationTemplates(), fetchNotificationLogs()]);
    setTemplates(t);
    setLogs(l);
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  const onSave = async (e: FormEvent) => {
    e.preventDefault();
    await saveNotificationTemplate({ ...form, is_active: true });
    setForm({ code: "", name: "", channel: "EMAIL", subject_template: "", body_template: "" });
    await load();
  };

  const onTest = async (code: string) => {
    await testSendNotification({
      template_code: code,
      recipient_email: testEmail,
      context: { donor_name: "Test", amount: "100", receipt_number: "RCP-TEST", category: "General" },
      idempotency_key: `test-${Date.now()}`,
    });
    await load();
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Notification center"
        description="Email, SMS, and WhatsApp templates with delivery logs and idempotency."
      />

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Templates</h2>
        <div className="mt-2 flex gap-2">
          <input
            placeholder="Test email"
            className="rounded border px-2 py-1 text-sm"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
          />
        </div>
        <ul className="mt-4 divide-y text-sm">
          {templates.map((t) => (
            <li key={t.id} className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium">
                  {t.code} · {t.channel}
                </p>
                <p className="text-stone-500">{t.name}</p>
              </div>
              <button
                type="button"
                onClick={() => onTest(t.code)}
                className="rounded border px-2 py-1 text-xs hover:bg-stone-50"
              >
                Test send
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="mb-4 font-semibold">Add template</h2>
        <form onSubmit={onSave} className="grid gap-3 sm:grid-cols-2">
          <input
            placeholder="Code"
            required
            className="rounded border px-3 py-2 text-sm"
            value={form.code}
            onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
          />
          <input
            placeholder="Name"
            required
            className="rounded border px-3 py-2 text-sm"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <select
            className="rounded border px-3 py-2 text-sm"
            value={form.channel}
            onChange={(e) => setForm((f) => ({ ...f, channel: e.target.value }))}
          >
            <option value="EMAIL">Email</option>
            <option value="SMS">SMS</option>
            <option value="WHATSAPP">WhatsApp</option>
          </select>
          <input
            placeholder="Subject (email)"
            className="rounded border px-3 py-2 text-sm"
            value={form.subject_template}
            onChange={(e) => setForm((f) => ({ ...f, subject_template: e.target.value }))}
          />
          <textarea
            placeholder="Body template with {{ variables }}"
            required
            className="col-span-2 rounded border px-3 py-2 text-sm"
            rows={4}
            value={form.body_template}
            onChange={(e) => setForm((f) => ({ ...f, body_template: e.target.value }))}
          />
          <button type="submit" className="rounded-lg bg-saffron-600 px-4 py-2 text-sm font-semibold text-white">
            Save template
          </button>
        </form>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Recent delivery log</h2>
        <ul className="mt-3 max-h-64 overflow-y-auto text-xs">
          {logs.map((l) => (
            <li key={l.id} className="border-b py-2">
              {l.created_at} · {l.template_code} · {l.channel} → {l.recipient}{" "}
              <span className={l.status === "SENT" ? "text-green-700" : "text-red-600"}>({l.status})</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
