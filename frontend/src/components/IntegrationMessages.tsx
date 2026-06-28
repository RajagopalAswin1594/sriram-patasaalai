"use client";

export type IntegrationMessage = {
  level: "info" | "warning" | "error";
  text: string;
  code?: string;
};

export type GitHubSyncResult = {
  attempted: boolean;
  success: boolean;
  mode: string;
  http_status?: number | null;
  issue_number?: number | null;
  issue_url?: string | null;
  error?: string;
  messages?: IntegrationMessage[];
};

const levelStyles: Record<IntegrationMessage["level"], string> = {
  info: "border-blue-200 bg-blue-50 text-blue-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  error: "border-red-200 bg-red-50 text-red-900",
};

export function IntegrationMessages({ messages }: { messages: IntegrationMessage[] }) {
  if (!messages.length) return null;
  return (
    <ul className="space-y-2">
      {messages.map((msg, i) => (
        <li key={`${msg.code ?? "msg"}-${i}`} className={`rounded-lg border px-4 py-3 text-sm ${levelStyles[msg.level]}`}>
          <span className="font-medium uppercase text-xs opacity-70">{msg.level}</span>
          <p className="mt-1">{msg.text}</p>
        </li>
      ))}
    </ul>
  );
}
