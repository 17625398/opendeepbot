/**
 * Auth Redirect Page
 * ===================
 *
 * 认证入口页面 — 将未登录用户重定向到登录页
 * Auth entry page that redirects unauthenticated users to the login page.
 */

"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

/**
 * 重定向逻辑（必须包裹在 Suspense 中，因为使用了 useSearchParams）
 * Redirect logic (must be wrapped in Suspense because it uses useSearchParams)
 */
function AuthRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get('from') || '/unified-chat';

  useEffect(() => {
    router.push(`/auth/login?from=${encodeURIComponent(from)}`);
  }, [from, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse">Redirecting...</div>
    </div>
  );
}

/** 带 Suspense 边界的主页面 / Main page with Suspense boundary */
export default function AuthPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse">Loading...</div>
      </div>
    }>
      <AuthRedirect />
    </Suspense>
  );
}
