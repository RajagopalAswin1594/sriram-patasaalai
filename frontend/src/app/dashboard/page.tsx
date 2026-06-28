"use client";

import { useAuth } from "@/components/AuthProvider";
import { PageHeader } from "@/components/PageHeader";

export default function DashboardPage() {
  const { me, hasPermission } = useAuth();

  const cards = [
    { label: "Users", permission: "users.view", href: "/dashboard/users" },
    { label: "Roles", permission: "roles.view", href: "/dashboard/roles" },
    { label: "Branches", permission: "branches.view", href: "/dashboard/branches" },
    { label: "Admissions", permission: "admissions.view", href: "/dashboard/admissions" },
    { label: "Audit", permission: "audit.view", href: "/dashboard/audit" },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Sprint 1 foundation platform for Gurukulam administration."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards
          .filter((card) => hasPermission(card.permission))
          .map((card) => (
            <a
              key={card.label}
              href={card.href}
              className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm transition hover:border-saffron-300"
            >
              <p className="text-lg font-semibold text-stone-900">{card.label}</p>
              <p className="mt-1 text-sm text-stone-500">Manage {card.label.toLowerCase()}</p>
            </a>
          ))}
      </div>
      <div className="mt-8 rounded-xl border border-stone-200 bg-white p-6">
        <h3 className="font-semibold text-stone-900">Session</h3>
        <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          <div>
            <dt className="text-stone-500">User type</dt>
            <dd className="font-medium">{me?.user.user_type}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Status</dt>
            <dd className="font-medium">{me?.user.account_status}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Roles</dt>
            <dd className="font-medium">{me?.user.roles.map((r) => r.role__name).join(", ") || "—"}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Permissions</dt>
            <dd className="font-medium">{me?.is_super_admin ? "All (*)" : me?.permissions.length}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
