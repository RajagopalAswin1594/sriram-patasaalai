"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";

const tabs = [
  { href: "/dashboard/feedback/submit", label: "Submit", permission: "feedback.add", superAdminOnly: true },
  { href: "/dashboard/feedback/mine", label: "Dev Queue", permission: "feedback.view", superAdminOnly: true },
  { href: "/dashboard/feedback/ops", label: "Dev Ops", permission: "feedback.manage", superAdminOnly: true },
];

export function FeedbackSubnav() {
  const pathname = usePathname();
  const { hasPermission, me } = useAuth();

  const visible = tabs.filter((t) => hasPermission(t.permission) && (!t.superAdminOnly || me?.is_super_admin));

  return (
    <nav className="flex flex-wrap gap-2 border-b border-stone-200 pb-4">
      {visible.map((tab) => {
        const active = pathname === tab.href || pathname.startsWith(`${tab.href}/`);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              active ? "bg-saffron-100 text-saffron-900" : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
