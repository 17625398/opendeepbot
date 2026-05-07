"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";

export default function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, loading, checkAuth } = useAuthStore();
  const from = searchParams.get('from') || '/unified-chat';

  useEffect(() => {
    // 检查认证状态
    if (!loading) {
      checkAuth();
    }
  }, []);

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        // 已认证，跳转到目标页面
        router.push(from);
      } else {
        // 未认证，跳转到登录页
        router.push(`/auth/login?from=${encodeURIComponent(from)}`);
      }
    }
  }, [isAuthenticated, loading, from, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse">Loading...</div>
    </div>
  );
}
