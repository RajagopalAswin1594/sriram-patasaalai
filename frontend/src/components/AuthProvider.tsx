"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { fetchMe, getStoredTokens, login as apiLogin, logout as apiLogout, setStoredBranchId } from "@/lib/api";
import { portalPathForUserType } from "@/lib/portal";
import type { MeResponse } from "@/lib/types";

type AuthContextValue = {
  me: MeResponse | null;
  loading: boolean;
  login: (email: string, password: string, branchId?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
  setBranchId: (branchId: string) => void;
  hasPermission: (codename: string) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshMe = useCallback(async () => {
    const tokens = getStoredTokens();
    if (!tokens) {
      setMe(null);
      return;
    }
    const data = await fetchMe();
    setMe(data);
    const primary = data.user.branches.find((b) => b.is_primary);
    if (primary && !data.branch_id) {
      setStoredBranchId(primary.branch_id);
    }
  }, []);

  useEffect(() => {
    refreshMe()
      .catch(() => setMe(null))
      .finally(() => setLoading(false));
  }, [refreshMe]);

  const login = async (email: string, password: string, branchId?: string) => {
    await apiLogin(email, password, branchId);
    const data = await fetchMe();
    setMe(data);
    router.push(portalPathForUserType(data.user.user_type));
  };

  const logout = async () => {
    await apiLogout();
    setMe(null);
    router.push("/login");
  };

  const setBranchId = (branchId: string) => {
    setStoredBranchId(branchId);
    refreshMe().catch(() => setMe(null));
  };

  const hasPermission = useCallback(
    (codename: string) => {
      if (!me) return false;
      if (me.is_super_admin || me.permissions.includes("*")) return true;
      return me.permissions.includes(codename);
    },
    [me],
  );

  const value = useMemo(
    () => ({ me, loading, login, logout, refreshMe, setBranchId, hasPermission }),
    [me, loading, refreshMe, hasPermission],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
