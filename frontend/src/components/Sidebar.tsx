"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";

const navItems = [
  { href: "/dashboard", label: "Dashboard", permission: null },
  { href: "/dashboard/users", label: "Users", permission: "users.view" },
  { href: "/dashboard/roles", label: "Roles", permission: "roles.view" },
  { href: "/dashboard/branches", label: "Branches", permission: "branches.view" },
  { href: "/dashboard/admissions", label: "Admissions", permission: "admissions.view" },
  { href: "/dashboard/students", label: "Students", permission: "students.view" },
  { href: "/dashboard/academics", label: "Academics", permission: "academics.view" },
  { href: "/dashboard/scheduling", label: "Scheduling", permission: "scheduling.view" },
  { href: "/dashboard/curriculum", label: "Curriculum", permission: "curriculum.view" },
  { href: "/dashboard/learning", label: "Learning", permission: "learning.view" },
  { href: "/dashboard/hostel", label: "Hostel", permission: "hostel.view" },
  { href: "/dashboard/donations", label: "Donations", permission: "donations.view" },
  { href: "/dashboard/notifications", label: "Notifications", permission: "notifications.view" },
  { href: "/dashboard/community", label: "Community", permission: "community.moderate" },
  { href: "/dashboard/gurukulam-feedback", label: "Gurukulam Feedback", permission: "gurukulam_feedback.manage" },
  { href: "/dashboard/feedback/submit", label: "App Dev Feedback", permission: "feedback.add" },
  { href: "/dashboard/feedback/ops", label: "Dev Feedback Ops", permission: "feedback.manage" },
  { href: "/dashboard/audit", label: "Audit", permission: "audit.view" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { me, logout, hasPermission } = useAuth();

  return (
    <aside className="flex w-64 flex-col border-r border-stone-200 bg-white">
      <div className="border-b border-stone-200 px-6 py-5">
        <Link href="/dashboard" className="group block">
          <p className="text-xs font-semibold uppercase tracking-widest text-saffron-700 group-hover:text-saffron-800">
            Gurukulam ERP
          </p>
          <h1 className="mt-1 text-lg font-semibold text-stone-900 group-hover:text-saffron-900">Foundation Platform</h1>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems
          .filter((item) => !item.permission || hasPermission(item.permission))
          .map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active ? "bg-saffron-100 text-saffron-900" : "text-stone-600 hover:bg-stone-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
      </nav>
      <div className="border-t border-stone-200 p-4">
        <p className="truncate text-sm font-medium text-stone-900">{me?.user.profile.display_name || me?.user.email}</p>
        <p className="truncate text-xs text-stone-500">{me?.user.user_type}</p>
        <button
          type="button"
          onClick={() => logout()}
          className="mt-3 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
