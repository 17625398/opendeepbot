import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Authentication Middleware / 认证中间件
 * Protects routes by checking for access token
 * 通过检查 access token 保护路由
 */

// Public routes list / 公开路由列表
const publicRoutes = [
  '/auth',
  '/auth/login',
  '/auth/register',
  '/login',
  '/home',
  '/share/',
];

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Check if the route is public / 检查是否为公开路由
  const isPublicRoute = publicRoutes.some(route =>
    path === route || path.startsWith(route + '/')
  );

  // Get token from cookies / 从 cookie 获取 token
  const token = request.cookies.get('access_token')?.value;

  // Allow public routes to pass through / 公开路由直接放行
  if (isPublicRoute) {
    return NextResponse.next();
  }

  // Redirect to login if no token / 如果没有 token 则重定向到登录页
  if (!token) {
    const url = new URL('/auth', request.nextUrl.origin);
    url.searchParams.set('from', path);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * 匹配所有请求路径，除以下路径外：
     * - api/ (API routes / API 路由)
     * - _next/static/ (static files / 静态文件)
     * - _next/image/ (image optimization files / 图片优化文件)
     * - favicon.ico (favicon file / 网站图标)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
