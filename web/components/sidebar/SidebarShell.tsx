"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { useAppShell } from "@/context/AppShellContext";
import {
  BookOpen,
  Bot,
  Brain,
  Github,
  Library,
  MessageSquare,
  Microscope,
  PanelLeftClose,
  PanelLeftOpen,
  PenLine,
  Plus,
  Search,
  Settings,
  Calculator,
  Globe,
  Sparkles,
  Clock3,
  NotebookPen,
  Layout,
  Shield,
  Boxes,
  Code2,
  Network,
  Workflow,
  ChevronDown,
  ChevronRight,
  type LucideIcon,
  BarChart3,
  FlaskRound,
  Scale,
  Wrench,
  FileSearch,
  FileCode,
  Edit3,
  Lightbulb,
  BrainCircuit,
  Database,
  GitBranch,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import SessionList from "@/components/SessionList";
import { TutorBotRecent } from "@/components/sidebar/TutorBotRecent";
import { BookRecent } from "@/components/sidebar/BookRecent";
import { CoWriterRecent } from "@/components/sidebar/CoWriterRecent";
import { VersionBadge } from "@/components/sidebar/VersionBadge";
import type { SessionSummary } from "@/lib/session-api";

interface NavEntry {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface NavGroup {
  id: string;
  label: string;
  items: NavEntry[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    id: "core",
    label: "Core",
    items: [
      { href: "/chat", label: "Chat", icon: MessageSquare },
      { href: "/deeptutor-chat", label: "DeepTutor", icon: Network },
      { href: "/knowledge-extraction", label: "Knowledge", icon: Brain },
      { href: "/agents", label: "TutorBot", icon: Bot },
      { href: "/research", label: "Research", icon: Microscope },
      { href: "/question", label: "Question", icon: Search },
      { href: "/solver", label: "Solver", icon: Calculator },
      { href: "/browser", label: "Browser", icon: Globe },
    ],
  },
  {
    id: "hermes",
    label: "Hermes",
    items: [
      { href: "/hermes", label: "Hermes Agent", icon: BrainCircuit },
    ],
  },
  {
    id: "panels",
    label: "Panels",
    items: [
      { href: "/toolbox", label: "Toolbox", icon: Boxes },
      { href: "/security-panel", label: "Security Panel", icon: Shield },
      { href: "/workflow-panel", label: "Workflow Panel", icon: Workflow },
    ],
  },
  {
    id: "workspace",
    label: "Workspace",
    items: [
      { href: "/skills", label: "Skills", icon: Sparkles },
      { href: "/scheduler", label: "Scheduler", icon: Clock3 },
      { href: "/notebook", label: "Notebook", icon: NotebookPen },
      { href: "/workspace", label: "Workspace", icon: Layout },
      { href: "/co-writer", label: "Co-Writer", icon: PenLine },
      { href: "/book", label: "Book", icon: Library },
      { href: "/knowledge", label: "Knowledge", icon: BookOpen },
      { href: "/memory", label: "Memory", icon: Brain },
    ],
  },
  {
    id: "analysis",
    label: "Analysis",
    items: [
      { href: "/analysis", label: "Analysis", icon: BarChart3 },
      { href: "/unified-chat", label: "Unified Chat", icon: MessageSquare },
      { href: "/visualization", label: "Visualization", icon: Network },
      { href: "/knowledge-graph", label: "Knowledge Graph", icon: GitBranch },
      { href: "/deep-analyze-chat", label: "Deep Analyze", icon: BrainCircuit },
      { href: "/deep-analyze-new", label: "Deep Analyze New", icon: BrainCircuit },
    ],
  },
  {
    id: "interrogation",
    label: "Interrogation",
    items: [
      { href: "/interrogation", label: "Interrogation", icon: Microscope },
      { href: "/interrogation/record-analysis", label: "Record Analysis", icon: FileSearch },
      { href: "/interrogation/case-analysis", label: "Case Analysis", icon: BarChart3 },
      { href: "/interrogation/dashboard", label: "Dashboard", icon: Layout },
    ],
  },
  {
    id: "tools",
    label: "Tools",
    items: [
      { href: "/browser-automation", label: "Browser Auto", icon: Globe },
      { href: "/code-search", label: "Code Search", icon: FileSearch },
      { href: "/code-review", label: "Code Review", icon: FileCode },
      { href: "/editor", label: "Editor", icon: Edit3 },
    ],
  },
  {
    id: "legal",
    label: "Legal",
    items: [
      { href: "/legal", label: "Legal", icon: Scale },
      { href: "/legal/sentencing", label: "Sentencing", icon: Scale },
      { href: "/legal/prediction", label: "Prediction", icon: Lightbulb },
      { href: "/legal/kg", label: "Legal KG", icon: GitBranch },
    ],
  },
  {
    id: "research-labs",
    label: "Research Labs",
    items: [
      { href: "/self-improvement", label: "Self-Improve", icon: Lightbulb },
      { href: "/supermemory", label: "SuperMemory", icon: BrainCircuit },
      { href: "/paperbanana", label: "Paper Banana", icon: FlaskRound },
      { href: "/mindspider", label: "Mind Spider", icon: Database },
    ],
  },
];

const COLLAPSED_NAV = NAV_GROUPS.flatMap((group) => group.items);

const SECONDARY_NAV: NavEntry[] = [
  { href: "/settings", label: "Settings", icon: Settings },
];
const SIDEBAR_GROUPS_STORAGE_KEY = "deeptutor-sidebar-groups";
const DEFAULT_SESSION_VIEWPORT_CLASS_NAME = "max-h-[112px]";
const GITHUB_REPO_URL = "https://github.com/HKUDS/DeepTutor";

interface SidebarShellProps {
  sessions?: SessionSummary[];
  activeSessionId?: string | null;
  loadingSessions?: boolean;
  showSessions?: boolean;
  sessionViewportClassName?: string;
  onNewChat?: () => void;
  onSelectSession?: (sessionId: string) => void | Promise<void>;
  onRenameSession?: (sessionId: string, title: string) => void | Promise<void>;
  onDeleteSession?: (sessionId: string) => void | Promise<void>;
  footerSlot?: ReactNode;
}

export function SidebarShell({
  sessions = [],
  activeSessionId = null,
  loadingSessions = false,
  showSessions = false,
  sessionViewportClassName = DEFAULT_SESSION_VIEWPORT_CLASS_NAME,
  onNewChat,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  footerSlot,
}: SidebarShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useTranslation();
  const { sidebarCollapsed: collapsed, setSidebarCollapsed: setCollapsed } =
    useAppShell();
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    core: true,
    hermes: false,
    panels: false,
    workspace: false,
    analysis: false,
    interrogation: false,
    tools: false,
    legal: false,
    "research-labs": false,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(SIDEBAR_GROUPS_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Record<string, boolean>;
      setExpandedGroups((prev) => ({ ...prev, ...parsed }));
    } catch {
      // ignore invalid persisted state
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      SIDEBAR_GROUPS_STORAGE_KEY,
      JSON.stringify(expandedGroups),
    );
  }, [expandedGroups]);

  useEffect(() => {
    const activeGroup = NAV_GROUPS.find((group) =>
      group.items.some((item) => pathname?.startsWith(item.href)),
    );
    if (!activeGroup) return;

    setExpandedGroups((prev) => {
      if (prev[activeGroup.id]) return prev;
      return {
        ...prev,
        [activeGroup.id]: true,
      };
    });
  }, [pathname]);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  const handleNewChat = () => {
    if (onNewChat) {
      onNewChat();
      return;
    }
    router.push("/chat");
  };

  /* ---- Collapsed state ---- */
  if (collapsed) {
    return (
      <aside className="group/sb relative flex h-screen w-[60px] shrink-0 flex-col items-center bg-[var(--secondary)] py-3 transition-all duration-200">
        {/* Header: logo + collapse toggle (toggle replaces logo on hover) */}
        <div className="relative mb-2 flex h-9 w-9 items-center justify-center">
          <Link
            href="/"
            aria-label="DeepTutor"
            className="flex items-center justify-center transition-opacity duration-150 group-hover/sb:opacity-0"
          >
            <Image
              src="/logo-ver2.png"
              alt="DeepTutor"
              width={22}
              height={22}
              className="rounded-md"
            />
          </Link>
          <button
            onClick={() => setCollapsed(false)}
            className="absolute inset-0 flex items-center justify-center rounded-lg text-[var(--muted-foreground)] opacity-0 transition-all duration-150 hover:bg-[var(--background)]/60 hover:text-[var(--foreground)] group-hover/sb:opacity-100"
            aria-label={t("Expand sidebar")}
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>

        {/* New chat — visually distinct circular button */}
        <button
          onClick={handleNewChat}
          title={t("New Chat") as string}
          className="mb-2 flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)]/50 bg-[var(--background)]/40 text-[var(--foreground)] shadow-sm transition-all duration-150 hover:border-[var(--border)] hover:bg-[var(--background)]/80"
          aria-label={t("New Chat")}
        >
          <Plus size={16} strokeWidth={2.2} />
        </button>

        {/* Subtle divider */}
        <div className="my-1.5 h-px w-7 bg-[var(--border)]/40" />

        {/* Primary nav */}
        <nav className="flex w-full flex-col items-center gap-1 px-1.5">
          {COLLAPSED_NAV.map((item) => {
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                title={t(item.label) as string}
                className={`relative flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-150 ${
                  active
                    ? "bg-[var(--background)]/80 text-[var(--foreground)] shadow-sm"
                    : "text-[var(--muted-foreground)] hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
                }`}
              >
                {active && (
                  <span className="absolute -left-1.5 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-[var(--foreground)]/80" />
                )}
                <item.icon size={18} strokeWidth={active ? 2 : 1.6} />
              </Link>
            );
          })}
        </nav>

        <div className="flex-1" />

        {/* Secondary nav + footer */}
        <div className="flex w-full flex-col items-center gap-1 px-1.5">
          <div className="my-1 h-px w-7 bg-[var(--border)]/40" />
          {SECONDARY_NAV.map((item) => {
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                title={t(item.label) as string}
                className={`relative flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-150 ${
                  active
                    ? "bg-[var(--background)]/80 text-[var(--foreground)] shadow-sm"
                    : "text-[var(--muted-foreground)] hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
                }`}
              >
                {active && (
                  <span className="absolute -left-1.5 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-[var(--foreground)]/80" />
                )}
                <item.icon size={18} strokeWidth={active ? 2 : 1.6} />
              </Link>
            );
          })}
          {footerSlot}
          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noreferrer noopener"
            title="GitHub"
            aria-label="GitHub"
            className="mt-1 flex h-9 w-9 items-center justify-center rounded-xl text-[var(--muted-foreground)]/70 transition-colors hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
          >
            <Github size={15} strokeWidth={1.6} />
          </a>
          <VersionBadge collapsed />
        </div>
      </aside>
    );
  }

  /* ---- Expanded state ---- */
  return (
    <aside className="flex w-[220px] h-screen shrink-0 flex-col bg-[var(--secondary)] transition-all duration-200">
      {/* Header: logo + collapse toggle */}
      <div className="flex h-14 items-center justify-between px-4">
        <Link href="/" className="group flex items-center gap-2">
          <Image
            src="/logo-ver2.png"
            alt="DeepTutor"
            width={22}
            height={22}
            className="transition-transform duration-200 group-hover:scale-105"
          />
          <span className="text-[16px] font-semibold leading-none tracking-[-0.02em] text-[var(--foreground)]">
            DeepTutor
          </span>
        </Link>
        <button
          onClick={() => setCollapsed(true)}
          className="rounded-md p-1 text-[var(--muted-foreground)] transition-colors hover:text-[var(--foreground)]"
          aria-label={t("Collapse sidebar")}
        >
          <PanelLeftClose size={15} />
        </button>
      </div>

      {/* Primary nav */}
      <nav className="px-2 pt-1">
        <div className="space-y-3">
          <button
            onClick={handleNewChat}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--background)]/60 hover:text-[var(--foreground)]"
          >
            <Plus size={16} strokeWidth={2} />
            <span>{t("New Chat")}</span>
          </button>

          {NAV_GROUPS.map((group) => {
            const groupExpanded = expandedGroups[group.id] ?? false;
            const groupHasActiveItem = group.items.some((item) =>
              pathname?.startsWith(item.href),
            );
            return (
              <div key={group.id} className="space-y-1">
                <button
                  type="button"
                  onClick={() => toggleGroup(group.id)}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.08em] transition-colors ${
                    groupHasActiveItem
                      ? "bg-[var(--background)]/55 text-[var(--foreground)]"
                      : "text-[var(--muted-foreground)]/70 hover:bg-[var(--background)]/40 hover:text-[var(--foreground)]/80"
                  }`}
                >
                  <span>{`${t(group.label)} (${group.items.length})`}</span>
                  {groupExpanded ? (
                    <ChevronDown size={14} />
                  ) : (
                    <ChevronRight size={14} />
                  )}
                </button>
                <div
                  className={`grid transition-all duration-200 ease-out ${
                    groupExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  }`}
                >
                  <div className="overflow-hidden">
                    <div className="space-y-px pt-0.5">
                      {group.items.map((item) => {
                        const active = pathname?.startsWith(item.href);
                        const hasSessionsBelow =
                          item.href === "/chat" &&
                          showSessions &&
                          onSelectSession &&
                          onRenameSession &&
                          onDeleteSession;
                        const hasBots = item.href === "/agents";
                        const hasBooks = item.href === "/book";
                        const hasCoWriterDocs = item.href === "/co-writer";
                        return (
                          <div key={item.href}>
                            <Link
                              href={item.href}
                              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors ${
                                active
                                  ? "bg-[var(--background)]/70 font-medium text-[var(--foreground)]"
                                  : "text-[var(--muted-foreground)] hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
                              }`}
                            >
                              <item.icon size={16} strokeWidth={active ? 1.9 : 1.5} />
                              <span>{t(item.label)}</span>
                            </Link>
                            {hasSessionsBelow && (
                              <div className={`${sessionViewportClassName} overflow-y-auto`}>
                                <SessionList
                                  sessions={sessions}
                                  activeSessionId={activeSessionId}
                                  loading={loadingSessions}
                                  onSelect={onSelectSession}
                                  onRename={onRenameSession}
                                  onDelete={onDeleteSession}
                                  compact
                                />
                              </div>
                            )}
                            {hasBots && <TutorBotRecent />}
                            {hasCoWriterDocs && <CoWriterRecent />}
                            {hasBooks && <BookRecent />}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Secondary nav + footer */}
      <div className="border-t border-[var(--border)]/40 px-2 py-2">
        {SECONDARY_NAV.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors ${
                active
                  ? "bg-[var(--background)]/70 font-medium text-[var(--foreground)]"
                  : "text-[var(--muted-foreground)] hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
              }`}
            >
              <item.icon size={16} strokeWidth={active ? 1.9 : 1.5} />
              <span>{t(item.label)}</span>
            </Link>
          );
        })}
        {footerSlot}
        <div className="mt-0.5 flex items-center gap-0.5">
          <VersionBadge />
          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noreferrer noopener"
            title="GitHub"
            aria-label="GitHub"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--muted-foreground)]/55 transition-colors hover:bg-[var(--background)]/50 hover:text-[var(--muted-foreground)]"
          >
            <Github size={13} strokeWidth={1.7} />
          </a>
        </div>
      </div>
    </aside>
  );
}
