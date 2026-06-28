"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import type { Paginated, Role } from "@/lib/types";

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Paginated<Role>>("/roles/")
      .then((data) => setRoles(data.results))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Roles" description="System and custom roles with permission mappings." />
      <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-500">
            <tr>
              <th className="px-4 py-3">Code</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Scope</th>
              <th className="px-4 py-3">Permissions</th>
              <th className="px-4 py-3">System</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-4 py-6" colSpan={5}>Loading...</td></tr>
            ) : roles.map((role) => (
              <tr key={role.id} className="border-t border-stone-100">
                <td className="px-4 py-3 font-mono text-xs">{role.code}</td>
                <td className="px-4 py-3">{role.name}</td>
                <td className="px-4 py-3">{role.scope_type}</td>
                <td className="px-4 py-3">{role.permissions.length}</td>
                <td className="px-4 py-3">{role.is_system ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
