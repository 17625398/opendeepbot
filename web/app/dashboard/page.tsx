"use client";

/**
 * Dashboard 页面 - 美化版
 * 用户登录后的主仪表盘
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Bot,
  BookOpen,
  MessageSquare,
  Workflow,
  Shield,
  Users,
  Settings,
  History,
  Sparkles,
  TrendingUp,
  Clock,
  ChevronRight,
  Zap,
  FileText,
  Activity,
  Plus,
  ArrowUpRight,
  Network,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useRequireAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Button from "@/components/ui/button";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/i18n";

// 统计数据模拟数据 - 使用翻译键
const getStatsData = (t: (key: string) => string) => [
  { label: t("Total Conversations"), value: "128", change: "+12%", icon: MessageSquare, color: "from-blue-500 to-cyan-500", bgColor: "bg-blue-50 dark:bg-blue-900/20" },
  { label: t("Knowledge Documents"), value: "56", change: "+5%", icon: BookOpen, color: "from-amber-500 to-orange-500", bgColor: "bg-amber-50 dark:bg-amber-900/20" },
  { label: t("Workflows"), value: "12", change: "+2", icon: Workflow, color: "from-purple-500 to-pink-500", bgColor: "bg-purple-50 dark:bg-purple-900/20" },
  { label: t("Active Cases"), value: "8", change: "+1", icon: Shield, color: "from-emerald-500 to-teal-500", bgColor: "bg-emerald-50 dark:bg-emerald-900/20" },
];

// 快速访问卡片数据 - 使用翻译键
const getQuickAccessItems = (t: (key: string) => string) => [
  {
    id: "deeptutor-chat",
    title: "DeepTutor Chat",
    description: "多平台统一聊天系统",
    icon: Network,
    href: "/deeptutor-chat",
    color: "from-cyan-500 to-teal-600",
    shadowColor: "shadow-cyan-500/30",
    badge: "New",
  },
  {
    id: "assistant",
    title: t("AI Assistant"),
    description: t("Smart Q&A and knowledge retrieval"),
    icon: Bot,
    href: "/assistant",
    color: "from-blue-500 to-blue-600",
    shadowColor: "shadow-blue-500/30",
  },
  {
    id: "chat",
    title: t("Smart Chat"),
    description: t("Multi-turn conversation and deep communication"),
    icon: MessageSquare,
    href: "/chat",
    color: "from-emerald-500 to-emerald-600",
    shadowColor: "shadow-emerald-500/30",
    badge: "New",
  },
  {
    id: "knowledge",
    title: t("Knowledge Base"),
    description: t("Manage documents and knowledge resources"),
    icon: BookOpen,
    href: "/knowledge",
    color: "from-amber-500 to-amber-600",
    shadowColor: "shadow-amber-500/30",
  },
  {
    id: "workflow",
    title: t("Workflow"),
    description: t("Visual process orchestration"),
    icon: Workflow,
    href: "/workflow",
    color: "from-purple-500 to-purple-600",
    shadowColor: "shadow-purple-500/30",
  },
  {
    id: "interrogation",
    title: t("Interrogation Center"),
    description: t("Case analysis and investigation tools"),
    icon: Shield,
    href: "/interrogation",
    color: "from-rose-500 to-rose-600",
    shadowColor: "shadow-rose-500/30",
  },
  {
    id: "multi-agent",
    title: t("Multi-Agent Collaboration"),
    description: t("Multi-Agent orchestration and collaboration"),
    icon: Users,
    href: "/multi-agent",
    color: "from-indigo-500 to-indigo-600",
    shadowColor: "shadow-indigo-500/30",
    badge: "New",
  },
];

// 最近活动模拟数据 - 使用翻译键
const getRecentActivities = (t: (key: string) => string) => [
  { id: 1, action: t("Created new workflow"), target: "案件分析流程", time: "10 分钟前", icon: Workflow, color: "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400" },
  { id: 2, action: t("Uploaded document"), target: "法律知识库.pdf", time: "1 小时前", icon: BookOpen, color: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400" },
  { id: 3, action: t("Completed conversation"), target: "合同审查助手", time: "2 小时前", icon: MessageSquare, color: "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400" },
  { id: 4, action: t("Analyzed case"), target: "案例 #2024-001", time: "昨天", icon: Shield, color: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400" },
];

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const { lang } = useLanguage();
  const _t = (key: string) => t(lang, key);

  // 加载中状态
  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-slate-600 dark:text-slate-400">{_t("Loading")}...</span>
        </div>
      </div>
    );
  }

  // 未登录状态
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
            {_t("Welcome back")}！
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            {_t("Today is")} {new Date().toLocaleDateString(lang === "zh" ? "zh-CN" : "en-US", { 
              year: "numeric", 
              month: "long", 
              day: "numeric",
              weekday: "long"
            })}，{_t("Have a nice day")}！
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2" onClick={() => window.location.href = '/assistant'}>
            <Plus className="w-4 h-4" />
            {_t("New Conversation")}
          </Button>
          <Button size="sm" className="gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg shadow-blue-500/30" onClick={() => window.location.href = '/workflow'}>
            <Zap className="w-4 h-4" />
            {_t("Quick Start")}
          </Button>
        </div>
      </motion.div>

      {/* 统计数据 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {getStatsData(_t).map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 * index }}
            >
              <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-sm bg-white dark:bg-slate-900">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{stat.label}</p>
                      <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                        {stat.value}
                      </p>
                      <div className="flex items-center gap-1 mt-2">
                        <TrendingUp className="w-3 h-3 text-emerald-500" />
                        <p className="text-xs font-medium text-emerald-600">{stat.change}</p>
                        <span className="text-xs text-slate-400 ml-1">{_t("vs last month")}</span>
                      </div>
                    </div>
                    <div className={`w-14 h-14 ${stat.bgColor} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className={`w-7 h-7 bg-gradient-to-br ${stat.color} bg-clip-text`} style={{ color: 'transparent', backgroundClip: 'text', WebkitBackgroundClip: 'text' }} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* 快速访问 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-500" />
            {_t("Quick Access")}
          </h2>
          <Button variant="ghost" size="sm" className="text-slate-500" onClick={() => window.location.href = '/'}>
            {_t("View All")}
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {getQuickAccessItems(_t).map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.1 * index }}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                className="group bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all cursor-pointer shadow-sm hover:shadow-xl hover:shadow-blue-500/10 relative overflow-hidden"
                onClick={() => window.location.href = item.href}
              >
                {/* 背景渐变装饰 */}
                <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${item.color} opacity-5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:opacity-10 transition-opacity`} />
                
                <div className="flex items-start gap-4 relative z-10">
                  <div className={`w-12 h-12 bg-gradient-to-br ${item.color} ${item.shadowColor} rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {item.title}
                      </h3>
                      {item.badge && (
                        <span className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                      {item.description}
                    </p>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30 transition-colors">
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* 下方两栏布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 最近活动 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card className="border-0 shadow-sm bg-white dark:bg-slate-900">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                {_t("Recent Activities")}
              </CardTitle>
              <Button variant="ghost" size="sm" className="text-slate-500" onClick={() => window.location.href = '/history'}>
                {_t("View All")}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {getRecentActivities(_t).map((activity, index) => {
                  const Icon = activity.icon;
                  return (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: 0.1 * index }}
                      className="flex items-center gap-4 p-4 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group cursor-pointer"
                    >
                      <div className={`w-10 h-10 ${activity.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-900 dark:text-white">
                          {activity.action}{" "}
                          <span className="font-medium text-blue-600 dark:text-blue-400">
                            {activity.target}
                          </span>
                        </p>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                          {activity.time}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 快捷操作 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Card className="border-0 shadow-sm bg-white dark:bg-slate-900">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                {_t("Quick Actions")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-3 h-12 border-slate-200 dark:border-slate-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all group"
                  onClick={() => window.location.href = "/assistant"}
                >
                  <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  {_t("Start New Conversation")}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-3 h-12 border-slate-200 dark:border-slate-700 hover:border-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-all group"
                  onClick={() => window.location.href = "/knowledge"}
                >
                  <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <BookOpen className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  </div>
                  {_t("Upload Document")}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-3 h-12 border-slate-200 dark:border-slate-700 hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all group"
                  onClick={() => window.location.href = "/workflow"}
                >
                  <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Workflow className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  {_t("Create Workflow")}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-3 h-12 border-slate-200 dark:border-slate-700 hover:border-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all group"
                  onClick={() => window.location.href = "/interrogation"}
                >
                  <div className="w-8 h-8 rounded-lg bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Shield className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  </div>
                  {_t("New Case")}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-3 h-12 border-slate-200 dark:border-slate-700 hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all group"
                  onClick={() => window.location.href = "/multi-agent"}
                >
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Users className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  {_t("Multi-Agent Collaboration")}
                </Button>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-slate-400" />
                  {_t("System Status")}
                </h4>
                <div className="space-y-3">
                  {[
                    { name: _t("API Service"), status: _t("Running normally"), color: "bg-emerald-500" },
                    { name: _t("Database"), status: _t("Connected"), color: "bg-emerald-500" },
                    { name: _t("AI Engine"), status: _t("Ready"), color: "bg-emerald-500" },
                  ].map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 ${item.color} rounded-full animate-pulse`} />
                        <span className="text-sm font-medium text-emerald-600">{item.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
