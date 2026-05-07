"use client";

/**
 * Home Page / 首页
 * Root page that handles authentication redirect
 * 根页面，处理认证重定向
 */
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, loading, checkAuth } = useAuthStore();

  // Check authentication status first / 首先检查认证状态
  useEffect(() => {
    if (!loading) {
      checkAuth();
    }
  }, []);

  // Redirect based on authentication status / 根据认证状态重定向
  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        router.push('/dashboard');
      } else {
        router.push('/auth');
      }
    }
  }, [isAuthenticated, loading, checkAuth, router]);

  // Loading state / 加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-500 font-medium">Loading session...</span>
        </div>
      </div>
    );
  }

  return null;
}
