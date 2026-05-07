# DeepTutor Frontend React to Next.js Migration - Product Requirements Document
# DeepTutor 前端 React 到 Next.js 迁移 - 产品需求文档

## Overview / 概述
- **Summary / 概要**: Migrate DeepTutor frontend from React + react-router-dom to Next.js App Router architecture
  # 将 DeepTutor 前端从 React + react-router-dom 架构迁移到 Next.js App Router 架构
- **Purpose / 目的**: Leverage Next.js server-side rendering, automatic code splitting, better performance optimization and modern routing system
  # 利用 Next.js 的服务端渲染、自动代码分割、更好的性能优化和现代化的路由系统
- **Target Users / 目标用户**: Development team and end users / 开发团队和最终用户

## Goals / 目标
- Migrate old React routing configuration (`src/App.tsx`) to Next.js App Router
  # 将旧的 React 路由配置（`src/App.tsx`）迁移到 Next.js App Router
- Clean up old React entry files (`src/main.tsx`) / 清理旧的 React 入口文件（`src/main.tsx`）
- Ensure all pages use Next.js native routing / 确保所有页面都使用 Next.js 原生路由
- Maintain feature completeness and backward compatibility / 保持功能完整性和向后兼容性

## Non-Goals (Out of Scope) / 非目标（范围外）
- Do not modify business logic or component functionality / 不修改业务逻辑或组件功能
- Do not perform large-scale refactoring or performance optimization / 不进行大规模重构或性能优化
- Do not add new features / 不添加新功能

## Background & Context / 背景与上下文
Project current state / 项目当前状态：
- Already has `app/` directory with most pages' Next.js implementation
  # 已有 `app/` 目录，包含大部分页面的 Next.js 实现
- Old `src/App.tsx` contains react-router-dom routing configuration with lazy-loaded page components
  # 旧的 `src/App.tsx` 包含 react-router-dom 路由配置，懒加载多个页面组件
- There are duplicate page paths (such as `/chat`, `/dashboard`, `/settings`, etc.) existing in both old and new routing
  # 存在重复的页面路径（如 `/chat`, `/dashboard`, `/settings` 等）同时存在于旧路由和新路由中

## Functional Requirements / 功能需求
- **FR-1**: Remove `react-router-dom` dependency, use Next.js App Router
  # 移除 `react-router-dom` 依赖，使用 Next.js App Router
- **FR-2**: Delete old `src/App.tsx` and `src/main.tsx` files
  # 删除旧的 `src/App.tsx` 和 `src/main.tsx` 文件
- **FR-3**: Ensure all page routes work correctly in Next.js
  # 确保所有页面路由在 Next.js 中正常工作
- **FR-4**: Update authentication and layout components to fit Next.js pattern
  # 更新认证和布局组件以适应 Next.js 模式

## Non-Functional Requirements / 非功能需求
- **NFR-1**: Application startup time should not exceed 110% of previous
  # 迁移后应用启动时间不超过之前的 110%
- **NFR-2**: All page routes accessible without 404 errors
  # 所有页面路由可访问，无 404 错误
- **NFR-3**: Authentication protection mechanism works correctly
  # 认证保护机制正常工作

## Constraints / 约束条件
- **Technical / 技术**: Must maintain compatibility with existing backend APIs
  # 必须保持与现有后端 API 的兼容性
- **Dependencies / 依赖**: Need to maintain compatibility with all existing third-party libraries
  # 需要保持所有现有第三方库的兼容性

## Assumptions / 假设
- All page components already exist in `app/` directory
  # 所有页面组件已存在于 `app/` 目录中
- Authentication logic is already implemented in `context/`
  # 认证逻辑已在 `context/` 中实现

## Acceptance Criteria / 验收标准

### AC-1: Route Migration Complete / 路由迁移完成
- **Given / 前提**: Old `src/App.tsx` exists / 旧的 `src/App.tsx` 存在
- **When / 触发**: After migration / 迁移完成后
- **Then / 结果**: `src/App.tsx` and `src/main.tsx` deleted, `react-router-dom` dependency removed
  # `src/App.tsx` 和 `src/main.tsx` 被删除，`react-router-dom` 依赖被移除
- **Verification / 验证**: `programmatic` / `programmatic`

### AC-2: All Pages Accessible / 所有页面可访问
- **Given / 前提**: User visits any page route / 用户访问任意页面路由
- **When / 触发**: Application is running / 应用运行时
- **Then / 结果**: All pages load normally without 404 errors / 所有页面正常加载，无 404 错误
- **Verification / 验证**: `programmatic` / `programmatic`

### AC-3: Authentication Protection Works / 认证保护工作正常
- **Given / 前提**: Unauthenticated user accesses protected page / 未登录用户访问受保护页面
- **When / 触发**: Try to access `/dashboard` and other protected routes / 尝试访问 `/dashboard` 等受保护路由
- **Then / 结果**: User is redirected to login page / 用户被重定向到登录页面
- **Verification / 验证**: `human-judgment` / `human-judgment`

## Open Questions / 开放问题
- [ ] Whether to keep old `pages/` directory? / 是否需要保留旧的 `pages/` 目录？
- [ ] Are there specific pages that need special handling? / 是否有特定页面需要特殊处理？
