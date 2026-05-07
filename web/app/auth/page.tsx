"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get('from') || '/unified-chat';

  useEffect(() => {
    // 直接重定向到登录页面，不等待认证检查
    // Directly redirect to login page without waiting for auth check
    router.push(`/auth/login?from=${encodeURIComponent(from)}`);
  }, [from, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse">Redirecting...</div>
    </div>
  );
}
