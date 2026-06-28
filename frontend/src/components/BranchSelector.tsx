"use client";

import { useAuth } from "@/components/AuthProvider";

export function BranchSelector() {
  const { me, setBranchId } = useAuth();
  const branches = me?.user.branches ?? [];
  const current = me?.branch_id ?? branches.find((b) => b.is_primary)?.branch_id ?? "";

  if (branches.length === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="branch" className="text-sm text-stone-500">
        Branch
      </label>
      <select
        id="branch"
        value={current}
        onChange={(e) => setBranchId(e.target.value)}
        className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm"
      >
        {branches.map((branch) => (
          <option key={branch.branch_id} value={branch.branch_id}>
            {branch.branch__code} — {branch.branch__name}
          </option>
        ))}
      </select>
    </div>
  );
}
