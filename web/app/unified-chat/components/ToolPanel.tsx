"use client";

import React, { useEffect, useMemo, useState, useRef } from "react";
import Button from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Globe,
  Layout,
  Clock,
  X,
  Settings,
  Wrench,
  BookOpen,
  Play,
  Database,
  Search,
  FileText,
  Sparkles,
  Bot,
  Chrome,
  Terminal,
  Workflow,
  ChevronLeft,
  ChevronRight,
  Layers,
  Box,
  Grid3X3,
  List,
  FileSpreadsheet,
  Scale,
  Network,
  Star,
  History,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { TraeAgentPanel } from "./trae-agent";
import { DeerFlowPanel } from "./deerflow";
import { OnyxPanel } from "./onyx";
import { useToolSystem } from "../tools";
import { BrowserTool } from "../tools/BrowserTool";
import { CanvasTool } from "../tools/CanvasTool";
import { CronTool } from "../tools/CronTool";
import { SmartDocPanelV3 } from "./smartdoc";
import { BBBrowserPanel } from "./bbbrowser";
import { WebAccessPanel } from "./webaccess";
import { OpenCLIPanel } from "./opencli";
import { ObscuraBrowserPanel } from "./obscura/ObscuraBrowserPanel";
import { SkillWorkspacePanel } from "./skills";
import { PDFPanel } from "./pdf";
import { OpenKBPanel } from "@/components/openkb";
import GraphifyPanel from "./graphify/GraphifyPanel";
import LlamaIndexPanel from "./llamaindex/LlamaIndexPanel";
import { ForensicAnalysisPanel } from "./forensic_analysis";
import { BatchForensicAnalysisPanel } from "./batch_forensic_analysis";
import { useUnifiedChat } from "@/context/unified-chat/UnifiedChatContext";
import { apiUrl } from "@/lib/api";
import type { UnifiedChatToolPayload } from "@/app/unified-chat/lib/skills";

interface ToolPanelProps {
  onClose: () => void;
  defaultTab?: string;
  defaultSubTab?: string;
  defaultPayload?: UnifiedChatToolPayload;
}

type PanelView = "settings" | "skills" | "smartdoc" | "mcp" | "catalog" | "trae-agent" | "deerflow" | "onyx" | "pdf" | string;

interface McpToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
  enum?: any[];
}

interface McpToolInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  status: string;
  parameters: McpToolParameter[];
  use_count: number;
  icon?: string;
}

interface SkillInfo {
  name: string;
  full_name: string;
  version: string;
  description: string;
  author: string;
  category: string;
  skill_type: string;
  tags: string[];
  is_installed: boolean;
  installed_version?: string | null;
  install_count: number;
  rating: number;
}

interface SkillDetail extends SkillInfo {
  instructions: string;
  dependencies: { name: string; version: string; optional: boolean }[];
}

// 工具分组配置
interface ToolGroup {
  id: string;
  label: string;
  icon: React.ReactNode;
  tools: string[];
  color?: string;
}

function parseSkillInputs(instructions: string): { key: string; description: string }[] {
  const match = instructions.match(/##\s*输入\s*([\s\S]*?)(?:\n##\s+|$)/i);
  if (!match) return [];

  const section = match[1];
  const lines = section
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const result: { key: string; description: string }[] = [];
  for (const line of lines) {
    const item = line.replace(/^[-*]\s*/, "");
    const parts = item.split(":");
    if (parts.length < 2) continue;
    const key = parts[0].trim();
    const description = parts.slice(1).join(":").trim();
    if (!key) continue;
    result.push({ key, description });
  }
  return result;
}

function coerceParamValue(type: string, raw: any): any {
  if (raw === "" || raw === undefined) return raw;
  const t = type.toLowerCase();
  if (t === "integer" || t === "int") {
    const n = Number(raw);
    return Number.isFinite(n) ? Math.trunc(n) : raw;
  }
  if (t === "number" || t === "float" || t === "double") {
    const n = Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
  if (t === "boolean" || t === "bool") {
    if (typeof raw === "boolean") return raw;
    if (raw === "true") return true;
    if (raw === "false") return false;
    return !!raw;
  }
  if (t === "object" || t === "array" || t === "json") {
    if (typeof raw !== "string") return raw;
    try {
      return JSON.parse(raw);
    } catch {
      return raw;
    }
  }
  return raw;
}

export function ToolPanel({ onClose, defaultTab = "settings", defaultSubTab, defaultPayload }: ToolPanelProps) {
  const { tools, activeTool, setActiveTool, updateToolConfig, executeTool, toolResults } = useToolSystem();
  const { sendMessage, ragProvider, setRagProvider, enableRAG } = useUnifiedChat();
  const [view, setView] = useState<PanelView>(defaultTab as PanelView);
  const [activeGroup, setActiveGroup] = useState<string>("all");
  const [showAsGrid, setShowAsGrid] = useState(true);
  const [globalSearch, setGlobalSearch] = useState("");
  const [recentTools, setRecentTools] = useState<string[]>([]);
  // Sync from localStorage after mount (SSR-safe)
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("toolpanel_recent") || "[]");
      if (Array.isArray(stored) && stored.length > 0) setRecentTools(stored);
    } catch {}
  }, []);
  const tabsListRef = useRef<HTMLDivElement>(null);

  const [mcpTools, setMcpTools] = useState<McpToolInfo[]>([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [mcpError, setMcpError] = useState<string | null>(null);
  const [mcpSearch, setMcpSearch] = useState("");
  const [selectedMcpToolId, setSelectedMcpToolId] = useState<string | null>(null);
  const [mcpParams, setMcpParams] = useState<Record<string, any>>({});
  const [mcpExecuting, setMcpExecuting] = useState(false);

  const [catalogSkills, setCatalogSkills] = useState<SkillInfo[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);
  const [skillParams, setSkillParams] = useState<Record<string, string>>({});
  const [skillExecuting, setSkillExecuting] = useState(false);

  const [ragQuery, setRagQuery] = useState("");
  const [ragQuestion, setRagQuestion] = useState("");
  const [ragTopK, setRagTopK] = useState(3);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);
  const [ragProviderUsed, setRagProviderUsed] = useState<string | null>(null);
  const [ragResults, setRagResults] = useState<
    { document_id: string; chunk_id?: string; content: string; score: number; metadata?: Record<string, any> }[]
  >([]);

  useEffect(() => {
    setView(defaultTab as PanelView);
  }, [defaultTab]);

  const toolIcons: Record<string, React.ReactNode> = {
    browser: <Globe className="w-4 h-4" />,
    canvas: <Layout className="w-4 h-4" />,
    cron: <Clock className="w-4 h-4" />,
  };

  const localToolIds = useMemo(() => Object.keys(tools), [tools]);

  // Track recently used tools
  const trackRecentTool = (toolId: string) => {
    setRecentTools((prev) => {
      const next = [toolId, ...prev.filter((id) => id !== toolId)].slice(0, 5);
      try { localStorage.setItem("toolpanel_recent", JSON.stringify(next)); } catch {}
      return next;
    });
  };

  // 工具分组定义 — consolidated from 8 to 6 groups
  const toolGroups: ToolGroup[] = useMemo(() => {
    const explicitTools = ["settings", "smartdoc", "mcp", "catalog", "rag", "trae-agent", "deerflow", "obscura", "bbbrowser", "webaccess", "opencli", "pdf", "openkb", "graphify", "llamaindex", "forensic", "batch-forensic"];
    const uniqueLocalTools = localToolIds.filter(id => !explicitTools.includes(id));
    
    return [
      {
        id: "all",
        label: "全部",
        icon: <Grid3X3 className="w-4 h-4" />,
        tools: [...explicitTools, ...uniqueLocalTools],
      },
      {
        id: "core",
        label: "核心",
        icon: <Settings className="w-4 h-4" />,
        tools: ["settings", "skills", "rag", "mcp"],
        color: "text-blue-500",
      },
      {
        id: "agents",
        label: "智能体",
        icon: <Bot className="w-4 h-4" />,
        tools: ["skills", "trae-agent", "deerflow", "smartdoc"],
        color: "text-purple-500",
      },
      {
        id: "knowledge",
        label: "知识",
        icon: <Network className="w-4 h-4" />,
        tools: ["graphify", "llamaindex", "forensic", "batch-forensic", "openkb", "pdf"],
        color: "text-rose-500",
      },
      {
        id: "web",
        label: "网络",
        icon: <Globe className="w-4 h-4" />,
        tools: ["obscura", "bbbrowser", "webaccess", "opencli"],
        color: "text-green-500",
      },
      {
        id: "tools",
        label: "工具",
        icon: <Wrench className="w-4 h-4" />,
        tools: ["catalog", ...uniqueLocalTools],
        color: "text-orange-500",
      },
    ];
  }, [localToolIds]);

  // 获取当前组的所有工具（支持全局搜索过滤）
  const currentGroupTools = useMemo(() => {
    const group = toolGroups.find(g => g.id === activeGroup);
    const tools = group ? group.tools : toolGroups[0].tools;
    const q = globalSearch.trim().toLowerCase();
    if (!q) return tools;
    return tools.filter((id) => {
      const cfg = toolConfig[id];
      if (!cfg) return false;
      return (
        id.toLowerCase().includes(q) ||
        cfg.label.toLowerCase().includes(q) ||
        cfg.description.toLowerCase().includes(q)
      );
    });
  }, [activeGroup, toolGroups, globalSearch]);

  // Filtered recently used tools
  const recentFilteredTools = useMemo(() => {
    const q = globalSearch.trim().toLowerCase();
    return recentTools.filter((id) => {
      if (q && !id.toLowerCase().includes(q)) return false;
      return !!toolConfig[id];
    });
  }, [recentTools, globalSearch]);

  // 标签页滚动
  const scrollTabs = (direction: "left" | "right") => {
    if (tabsListRef.current) {
      const scrollAmount = 200;
      tabsListRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    if (view !== "mcp") return;
    if (mcpLoading) return;
    if (mcpTools.length > 0) return;

    let cancelled = false;
    (async () => {
      setMcpLoading(true);
      setMcpError(null);
      try {
        const res = await fetch(apiUrl("/api/v1/mcp/tools/list"));
        const json = await res.json();
        if (cancelled) return;
        setMcpTools(Array.isArray(json) ? json : []);
        const first = Array.isArray(json) && json.length > 0 ? json[0]?.id : null;
        setSelectedMcpToolId((prev) => prev ?? first);
      } catch (e) {
        if (cancelled) return;
        setMcpError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setMcpLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mcpLoading, mcpTools.length, view]);

  useEffect(() => {
    if (view !== "catalog") return;
    if (catalogLoading) return;
    if (catalogSkills.length > 0) return;

    let cancelled = false;
    (async () => {
      setCatalogLoading(true);
      setCatalogError(null);
      try {
        const res = await fetch(apiUrl("/api/v1/skill-catalog/skills"));
        const json = await res.json();
        if (cancelled) return;
        setCatalogSkills(Array.isArray(json) ? json : []);
      } catch (e) {
        if (cancelled) return;
        setCatalogError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [catalogLoading, catalogSkills.length, view]);

  useEffect(() => {
    if (!selectedMcpToolId) return;
    const tool = mcpTools.find((t) => t.id === selectedMcpToolId);
    if (!tool) return;
    const defaults: Record<string, any> = {};
    for (const p of tool.parameters || []) {
      if (p.default !== undefined) defaults[p.name] = p.default;
    }
    setMcpParams(defaults);
  }, [selectedMcpToolId, mcpTools]);

  const selectedMcpTool = useMemo(
    () => mcpTools.find((t) => t.id === selectedMcpToolId) || null,
    [mcpTools, selectedMcpToolId]
  );

  const filteredMcpTools = useMemo(() => {
    const q = mcpSearch.trim().toLowerCase();
    if (!q) return mcpTools;
    return mcpTools.filter(
      (t) =>
        t.id.toLowerCase().includes(q) ||
        t.name.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q)
    );
  }, [mcpTools, mcpSearch]);

  const filteredCatalogSkills = useMemo(() => {
    const q = catalogSearch.trim().toLowerCase();
    if (!q) return catalogSkills;
    return catalogSkills.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.tags.some((tag) => tag.toLowerCase().includes(q))
    );
  }, [catalogSkills, catalogSearch]);

  const handleExecuteMcp = async () => {
    if (!selectedMcpTool) return;
    setMcpExecuting(true);
    try {
      const body = { tool_id: selectedMcpTool.id, parameters: mcpParams };
      const res = await fetch(apiUrl("/api/v1/mcp/tools/execute"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || "执行失败");
      }
      sendMessage(
        `MCP 工具执行结果\n\n工具: ${selectedMcpTool.name}\n输出:\n${JSON.stringify(json, null, 2)}`
      );
    } catch (e) {
      sendMessage(`MCP 工具执行失败: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setMcpExecuting(false);
    }
  };

  const handleLoadSkillDetail = async (name: string) => {
    try {
      const res = await fetch(apiUrl(`/api/v1/skill-catalog/skills/${name}`));
      if (!res.ok) throw new Error("加载失败");
      const detail: SkillDetail = await res.json();
      setSelectedSkill(detail);
      const inputs = parseSkillInputs(detail.instructions);
      const initial: Record<string, string> = {};
      for (const i of inputs) initial[i.key] = "";
      setSkillParams(initial);
    } catch (e) {
      setCatalogError(e instanceof Error ? e.message : "加载详情失败");
    }
  };

  const handleExecuteSkill = async () => {
    if (!selectedSkill) return;
    setSkillExecuting(true);
    try {
      const body = { skill_name: selectedSkill.name, inputs: skillParams };
      const res = await fetch(apiUrl("/api/v1/skills/execute"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || "执行失败");
      }
      sendMessage(
        `技能执行结果\n\n技能: ${selectedSkill.name}\n输出:\n${JSON.stringify(json, null, 2)}`
      );
    } catch (e) {
      sendMessage(`技能执行失败: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSkillExecuting(false);
    }
  };

  const handleRagSearch = async () => {
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    setRagError(null);
    setRagResults([]);
    try {
      const res = await fetch(apiUrl("/api/v1/rag/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: ragQuery.trim(), top_k: ragTopK, provider: ragProvider }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "检索失败");
      setRagResults(json.results || []);
      setRagProviderUsed(json.provider_used || ragProvider);
    } catch (e) {
      setRagError(e instanceof Error ? e.message : "检索失败");
    } finally {
      setRagLoading(false);
    }
  };

  const handleRagAsk = async () => {
    if (!ragQuestion.trim()) return;
    setRagLoading(true);
    setRagError(null);
    try {
      const res = await fetch(apiUrl("/api/v1/rag/ask"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: ragQuestion.trim(), provider: ragProvider }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "问答失败");
      sendMessage(`RAG 问答\n\n问题: ${ragQuestion}\n\n回答:\n${json.answer || "无回答"}`);
    } catch (e) {
      setRagError(e instanceof Error ? e.message : "问答失败");
    } finally {
      setRagLoading(false);
    }
  };

  const renderToolContent = () => {
    switch (view) {
      case "smartdoc":
        return (
          <SmartDocPanelV3
            defaultTab={defaultSubTab}
            prefill={defaultPayload}
            onExtractedContent={(content, title) => {
              // 将提取的内容发送到聊天
              const message = title
                ? `我提取了网页内容："${title}"\n\n${content}`
                : content;
              sendMessage(message);
              onClose();
            }}
            onClose={onClose}
          />
        );
      case "trae-agent":
        return <TraeAgentPanel onClose={onClose} />;
      case "deerflow":
        return <DeerFlowPanel onClose={onClose} />;
      case "bbbrowser":
        return <BBBrowserPanel />;
      case "obscura":
        return <ObscuraBrowserPanel />;
      case "webaccess":
        return <WebAccessPanel defaultTab={defaultSubTab} prefill={defaultPayload} />;
      case "opencli":
        return (
          <OpenCLIPanel
            onClose={onClose}
            defaultTab={(defaultSubTab as "browser" | "builder" | "history" | undefined) || "browser"}
            prefill={defaultPayload}
          />
        );
      case "skills":
        return <SkillWorkspacePanel />;
      case "pdf":
        return <PDFPanel onClose={onClose} />;
      case "openkb":
        return <OpenKBPanel onClose={onClose} />;
      case "llamaindex":
        return <LlamaIndexPanel onClose={onClose} />;
      case "forensic":
          return <ForensicAnalysisPanel onClose={onClose} />;
        case "batch-forensic":
          return <BatchForensicAnalysisPanel onClose={onClose} />;
      case "interrogation":
        return (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 mx-auto mb-4 text-amber-500" />
            <h3 className="text-lg font-medium mb-2">案件笔录分析系统</h3>
            <p className="text-slate-500 mb-6">专业的案件笔录分析工具，支持多笔录关联分析</p>
            <Button onClick={() => {
              window.location.href = "/interrogation";
              onClose();
            }}>
              进入系统
            </Button>
          </div>
        );
      case "legal":
        return (
          <div className="p-8 text-center">
            <Scale className="w-12 h-12 mx-auto mb-4 text-amber-500" />
            <h3 className="text-lg font-medium mb-2">法律智能分析</h3>
            <p className="text-slate-500 mb-6">智能法律分析工具，支持法规匹配和案例分析</p>
            <Button onClick={() => {
              window.location.href = "/legal";
              onClose();
            }}>
              进入系统
            </Button>
          </div>
        );
      case "browser":
        return <BrowserTool />;
      case "canvas":
        return <CanvasTool />;
      case "cron":
        return <CronTool />;
      default:
        return (
          <div className="p-8 text-center text-slate-500">
            <Wrench className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>选择一个工具开始使用</p>
          </div>
        );
    }
  };

  // Shared handler for tool selection
  const selectTool = (toolId: string) => {
    setView(toolId);
    trackRecentTool(toolId);
    if (toolId === "settings" || toolId === "skills" || toolId === "mcp" || toolId === "catalog") {
      setActiveTool(null);
    } else if (localToolIds.includes(toolId)) {
      setActiveTool(toolId);
    } else {
      setActiveTool(null);
    }
  };

  // 渲染工具按钮
  const renderToolButton = (toolId: string, label: string, icon: React.ReactNode, description?: string) => {
    const isActive = view === toolId;
    const isEnabled = toolId === "settings" || toolId === "skills" || toolId === "smartdoc" || toolId === "mcp" || toolId === "catalog" || toolId === "rag" || toolId === "trae-agent" || toolId === "deerflow" || toolId === "obscura" || toolId === "bbbrowser" || toolId === "webaccess" || toolId === "opencli" || toolId === "pdf" || toolId === "graphify" || toolId === "llamaindex" || tools[toolId]?.config?.enabled;
    
    if (showAsGrid) {
      return (
        <TooltipProvider key={toolId}>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => { if (!isEnabled) return; selectTool(toolId); }}
                disabled={!isEnabled}
                className={cn(
                  "flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-200 group hover:shadow-sm",
                  isActive
                    ? "bg-primary/10 border-primary/40 ring-1 ring-primary/20 shadow-sm"
                    : "bg-card border-border/60 hover:border-primary/30 hover:bg-accent/50",
                  !isEnabled && "opacity-40 cursor-not-allowed"
                )}
              >
                <div className={cn(
                  "p-2.5 rounded-lg mb-1.5 transition-all duration-200",
                  isActive
                    ? "bg-primary/15 text-primary scale-110"
                    : "bg-muted text-muted-foreground group-hover:scale-105 group-hover:text-foreground"
                )}>
                  {icon}
                </div>
                <span className={cn(
                  "text-xs font-medium text-center leading-tight",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}>{label}</span>
              </button>
            </TooltipTrigger>
            {description && (
              <TooltipContent side="bottom" className="max-w-[200px]">
                <p className="text-xs">{description}</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      );
    }

    return (
      <TooltipProvider key={toolId}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => { if (!isEnabled) return; selectTool(toolId); }}
              disabled={!isEnabled}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 whitespace-nowrap",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground",
                !isEnabled && "opacity-40 cursor-not-allowed"
              )}
            >
              {icon}
              <span>{label}</span>
            </button>
          </TooltipTrigger>
          {description && (
            <TooltipContent side="bottom">
              <p>{description}</p>
            </TooltipContent>
          )}
        </Tooltip>
      </TooltipProvider>
    );
  };

  // 工具配置映射
  const toolConfig: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
    settings: { label: "设置", icon: <Settings className="w-4 h-4" />, description: "工具配置和系统设置" },
    skills: { label: "技能", icon: <Sparkles className="w-4 h-4" />, description: "统一聊天技能工作区" },
    smartdoc: { label: "SmartDoc", icon: <FileText className="w-4 h-4" />, description: "智能文档处理与提取" },
    pdf: { label: "PDF", icon: <FileSpreadsheet className="w-4 h-4" />, description: "PDF 文本提取和转换" },
    mcp: { label: "MCP", icon: <Wrench className="w-4 h-4" />, description: "MCP 工具协议管理" },
    catalog: { label: "目录", icon: <BookOpen className="w-4 h-4" />, description: "技能目录与发现" },
    rag: { label: "RAG", icon: <Database className="w-4 h-4" />, description: "知识库检索与问答" },
    "trae-agent": { label: "Trae", icon: <Bot className="w-4 h-4" />, description: "AI 编码助手与代码生成" },
    deerflow: { label: "DeerFlow", icon: <Workflow className="w-4 h-4" />, description: "多代理工作流编排" },
    obscura: { label: "Obscura", icon: <Chrome className="w-4 h-4" />, description: "统一聊天浏览器运行时" },
    bbbrowser: { label: "浏览器", icon: <Globe className="w-4 h-4" />, description: "浏览器自动化操作" },
    webaccess: { label: "Web", icon: <Terminal className="w-4 h-4" />, description: "网页内容访问工具" },
    opencli: { label: "CLI", icon: <Terminal className="w-4 h-4" />, description: "命令行远程执行" },
    browser: { label: "浏览器", icon: <Globe className="w-4 h-4" />, description: "浏览器工具" },
    canvas: { label: "画布", icon: <Layout className="w-4 h-4" />, description: "可视化画布与图表" },
    cron: { label: "定时", icon: <Clock className="w-4 h-4" />, description: "定时任务调度" },
    openkb: { label: "OpenKB", icon: <BookOpen className="w-4 h-4" />, description: "知识库管理与维护" },
    graphify: { label: "Graphify", icon: <Network className="w-4 h-4" />, description: "代码知识图谱构建与查询" },
    llamaindex: { label: "LlamaIndex", icon: <Database className="w-4 h-4" />, description: "LlamaIndex RAG 框架集成" },
    forensic: { label: "法证分析", icon: <FileText className="w-4 h-4" />, description: "案件笔录与电子证据分析" },
    "batch-forensic": { label: "批量分析", icon: <Layers className="w-4 h-4" />, description: "批量案件笔录与证据分析" },
  };

  return (
    <Card className="w-[520px] h-full border-l shadow-lg flex flex-col">
      {/* 头部 */}
      <CardHeader className="flex flex-row items-center justify-between pb-3 shrink-0">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="p-1.5 rounded-md bg-primary/10">
            <Wrench className="w-5 h-5 text-primary" />
          </div>
          工具箱
          <Badge variant="secondary" className="text-xs font-normal">
            {currentGroupTools.length} 个工具
          </Badge>
        </CardTitle>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setShowAsGrid(!showAsGrid)}
            title={showAsGrid ? "列表视图" : "网格视图"}
          >
            {showAsGrid ? <List className="w-4 h-4" /> : <Grid3X3 className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0 flex-1 flex flex-col min-h-0">
        {/* 全局搜索栏 */}
        <div className="px-4 pt-3 pb-2 shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              placeholder="搜索工具名称或描述..."
              className="pl-9 h-9 text-sm"
            />
            {globalSearch && (
              <button
                onClick={() => setGlobalSearch("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* 最近使用（仅在非搜索时显示） */}
        {!globalSearch && recentFilteredTools.length > 0 && (
          <div className="px-4 pb-2 shrink-0">
            <div className="flex items-center gap-1.5 mb-2 text-xs text-muted-foreground">
              <History className="w-3.5 h-3.5" />
              <span>最近使用</span>
            </div>
            <div className="flex items-center gap-2 overflow-x-auto">
              {recentFilteredTools.map((toolId) => {
                const cfg = toolConfig[toolId];
                if (!cfg) return null;
                return (
                  <button
                    key={toolId}
                    onClick={() => {
                      setView(toolId);
                      trackRecentTool(toolId);
                    }}
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all shrink-0",
                      view === toolId
                        ? "bg-primary/10 text-primary border border-primary/30"
                        : "bg-muted/60 text-muted-foreground border border-transparent hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {cfg.icon}
                    <span>{cfg.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* 分组选择器 */}
        <div className="px-4 pb-2 border-b shrink-0">
          <div className="flex items-center gap-1 p-1 bg-muted/50 rounded-lg overflow-x-auto">
            {toolGroups.map((group) => {
              const groupToolCount = activeGroup === group.id
                ? currentGroupTools.length
                : group.tools.filter((id) => toolConfig[id]).length;
              return (
                <button
                  key={group.id}
                  onClick={() => { setActiveGroup(group.id); setGlobalSearch(""); }}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 whitespace-nowrap",
                    activeGroup === group.id
                      ? "bg-background text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  <span className={cn(activeGroup === group.id && group.color)}>{group.icon}</span>
                  <span>{group.label}</span>
                  <span className={cn(
                    "ml-0.5 text-[10px] px-1 rounded",
                    activeGroup === group.id
                      ? "bg-primary/10 text-primary"
                      : "bg-muted-foreground/10 text-muted-foreground"
                  )}>
                    {groupToolCount}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 工具选择区域 */}
        <div className="border-b shrink-0">
          <div className="relative">
            {/* 滚动按钮（仅在列表模式显示） */}
            {!showAsGrid && (
              <>
                <button
                  onClick={() => scrollTabs("left")}
                  className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-full shadow-sm border opacity-0 hover:opacity-100 transition-opacity"
                >
                  <ChevronLeft className="w-3 h-3" />
                </button>
                <button
                  onClick={() => scrollTabs("right")}
                  className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-full shadow-sm border opacity-0 hover:opacity-100 transition-opacity"
                >
                  <ChevronRight className="w-3 h-3" />
                </button>
              </>
            )}

            {/* 工具列表 */}
            <ScrollArea className="w-full">
              <div
                ref={tabsListRef}
                className={cn(
                  "p-3",
                  showAsGrid
                    ? "grid grid-cols-4 gap-2"
                    : "flex items-center gap-2 flex-nowrap"
                )}
              >
                {currentGroupTools.length === 0 ? (
                  <div className="col-span-4 py-6 text-center text-sm text-muted-foreground">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    未找到匹配的工具
                  </div>
                ) : (
                  currentGroupTools.map((toolId) => {
                    const config = toolConfig[toolId];
                    if (!config) return null;
                    return renderToolButton(toolId, config.label, config.icon, config.description);
                  })
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={view} className="h-full flex flex-col">
            <TabsContent value="settings" className="m-0 p-4 flex-1 overflow-auto">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">工具配置</h3>
                  <Badge variant="outline" className="text-xs">
                    {Object.keys(tools).length} 个本地工具
                  </Badge>
                </div>
                <div className="space-y-2">
                  {Object.entries(tools).map(([id, tool]) => (
                    <div
                      key={id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:border-primary/30 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                          {toolIcons[id]}
                        </div>
                        <div>
                          <p className="font-medium text-sm">{tool.name}</p>
                          <p className="text-xs text-slate-500">{tool.description}</p>
                        </div>
                      </div>
                      <Switch
                        checked={tool.config.enabled}
                        onCheckedChange={(checked) =>
                          updateToolConfig(id, { enabled: checked })
                        }
                      />
                    </div>
                  ))}
                </div>
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
                    💡 使用提示
                  </h4>
                  <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
                    <li>• 浏览器工具：自动化网页访问、截图、数据提取</li>
                    <li>• 可视化画布：创建流程图、思维导图、时间线</li>
                    <li>• 定时任务：设置自动执行的分析任务</li>
                  </ul>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="skills" className="m-0 flex-1 overflow-hidden">
              <SkillWorkspacePanel />
            </TabsContent>

            <TabsContent value="mcp" className="m-0 flex-1 overflow-hidden">
              <div className="h-full flex flex-col p-4">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <Input
                    value={mcpSearch}
                    onChange={(e) => setMcpSearch(e.target.value)}
                    placeholder="搜索 MCP 工具（id/name/分类）"
                    className="flex-1"
                  />
                </div>
                {mcpError && (
                  <div className="text-sm text-red-600 mb-2">{mcpError}</div>
                )}
                <div className="flex-1 grid grid-cols-2 gap-3 overflow-hidden">
                  <Card className="h-full overflow-hidden">
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm">工具列表</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 h-[calc(100%-3rem)]">
                      <ScrollArea className="h-full">
                        <div className="p-2 space-y-1">
                          {mcpLoading ? (
                            <div className="text-sm text-slate-500 p-2">加载中...</div>
                          ) : filteredMcpTools.length === 0 ? (
                            <div className="text-sm text-slate-500 p-2">暂无工具</div>
                          ) : (
                            filteredMcpTools.map((t) => (
                              <button
                                key={t.id}
                                type="button"
                                onClick={() => setSelectedMcpToolId(t.id)}
                                className={cn(
                                  "w-full text-left p-2 rounded border transition-colors",
                                  selectedMcpToolId === t.id
                                    ? "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700"
                                    : "hover:bg-slate-50 dark:hover:bg-slate-900 border-transparent"
                                )}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <div className="font-medium text-sm truncate">{t.name}</div>
                                  <Badge variant="secondary" className="text-[10px]">
                                    {t.category}
                                  </Badge>
                                </div>
                                <div className="text-xs text-slate-500 truncate">{t.id}</div>
                              </button>
                            ))
                          )}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  <Card className="h-full overflow-hidden">
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm">执行</CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 h-[calc(100%-3rem)] overflow-hidden">
                      {!selectedMcpTool ? (
                        <div className="text-sm text-slate-500">选择一个工具</div>
                      ) : (
                        <div className="h-full flex flex-col overflow-hidden">
                          <div className="mb-3">
                            <div className="font-medium">{selectedMcpTool.name}</div>
                            <div className="text-xs text-slate-500">{selectedMcpTool.description}</div>
                            <div className="text-xs text-slate-500 mt-1">{selectedMcpTool.id}</div>
                          </div>
                          <ScrollArea className="flex-1">
                            <div className="space-y-3 pr-3">
                              {(selectedMcpTool.parameters ?? []).length === 0 ? (
                                <div className="text-sm text-slate-500">无参数</div>
                              ) : (
                                selectedMcpTool.parameters.map((p) => (
                                  <div key={p.name} className="space-y-1">
                                    <div className="flex items-center justify-between gap-2">
                                      <div className="text-sm font-medium">
                                        {p.name}
                                        {p.required ? (
                                          <span className="text-red-500 ml-1">*</span>
                                        ) : null}
                                      </div>
                                      <div className="text-xs text-slate-500">{p.type}</div>
                                    </div>
                                    <div className="text-xs text-slate-500">{p.description}</div>
                                    {p.enum ? (
                                      <Select
                                        value={String(mcpParams[p.name] ?? "")}
                                        onValueChange={(v) =>
                                          setMcpParams((prev) => ({ ...prev, [p.name]: v }))
                                        }
                                      >
                                        <SelectTrigger className="w-full">
                                          <SelectValue placeholder="选择值" />
                                        </SelectTrigger>
                                        <SelectContent>
                                          {p.enum.map((ev) => (
                                            <SelectItem key={String(ev)} value={String(ev)}>
                                              {String(ev)}
                                            </SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                    ) : (
                                      <Input
                                        value={mcpParams[p.name] ?? ""}
                                        onChange={(e) =>
                                          setMcpParams((prev) => ({
                                            ...prev,
                                            [p.name]: coerceParamValue(p.type, e.target.value),
                                          }))
                                        }
                                        placeholder={p.default !== undefined ? String(p.default) : ""}
                                      />
                                    )}
                                  </div>
                                ))
                              )}
                              <Button
                                onClick={handleExecuteMcp}
                                disabled={mcpExecuting}
                                className="w-full"
                              >
                                {mcpExecuting ? "执行中..." : "执行"}
                              </Button>
                            </div>
                          </ScrollArea>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="catalog" className="m-0 flex-1 overflow-hidden">
              <div className="h-full flex flex-col p-4">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <Input
                    value={catalogSearch}
                    onChange={(e) => setCatalogSearch(e.target.value)}
                    placeholder="搜索技能（名称/描述/标签）"
                    className="flex-1"
                  />
                </div>
                {catalogError && (
                  <div className="text-sm text-red-600 mb-2">{catalogError}</div>
                )}
                <div className="flex-1 grid grid-cols-2 gap-3 overflow-hidden">
                  <Card className="h-full overflow-hidden">
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm">技能列表</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 h-[calc(100%-3rem)]">
                      <ScrollArea className="h-full">
                        <div className="p-2 space-y-1">
                          {catalogLoading ? (
                            <div className="text-sm text-slate-500 p-2">加载中...</div>
                          ) : filteredCatalogSkills.length === 0 ? (
                            <div className="text-sm text-slate-500 p-2">暂无技能</div>
                          ) : (
                            filteredCatalogSkills.map((s) => (
                              <button
                                key={s.name}
                                type="button"
                                onClick={() => handleLoadSkillDetail(s.name)}
                                className={cn(
                                  "w-full text-left p-2 rounded border transition-colors",
                                  selectedSkill?.name === s.name
                                    ? "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700"
                                    : "hover:bg-slate-50 dark:hover:bg-slate-900 border-transparent"
                                )}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <div className="font-medium text-sm truncate">{s.name}</div>
                                  <Badge variant="secondary" className="text-[10px]">
                                    {s.category}
                                  </Badge>
                                </div>
                                <div className="text-xs text-slate-500 truncate">{s.description}</div>
                              </button>
                            ))
                          )}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  <Card className="h-full overflow-hidden">
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm">执行</CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 h-[calc(100%-3rem)] overflow-hidden">
                      {!selectedSkill ? (
                        <div className="text-sm text-slate-500">选择一个技能</div>
                      ) : (
                        <div className="h-full flex flex-col overflow-hidden">
                          <div className="mb-3">
                            <div className="font-medium">{selectedSkill.name}</div>
                            <div className="text-xs text-slate-500">{selectedSkill.description}</div>
                          </div>
                          <ScrollArea className="flex-1">
                            <div className="space-y-3 pr-3">
                              {parseSkillInputs(selectedSkill.instructions).length === 0 ? (
                                <div className="text-sm text-slate-500">无输入参数</div>
                              ) : (
                                parseSkillInputs(selectedSkill.instructions).map((input) => (
                                  <div key={input.key} className="space-y-1">
                                    <div className="text-sm font-medium">{input.key}</div>
                                    <div className="text-xs text-slate-500">{input.description}</div>
                                    <Input
                                      value={skillParams[input.key] ?? ""}
                                      onChange={(e) =>
                                        setSkillParams((prev) => ({
                                          ...prev,
                                          [input.key]: e.target.value,
                                        }))
                                      }
                                      placeholder={`输入 ${input.key}`}
                                    />
                                  </div>
                                ))
                              )}
                              <Button
                                onClick={handleExecuteSkill}
                                disabled={skillExecuting}
                                className="w-full"
                              >
                                {skillExecuting ? "执行中..." : "执行"}
                              </Button>
                            </div>
                          </ScrollArea>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="rag" className="m-0 p-4 flex-1 overflow-auto">
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-3">RAG 知识库</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium mb-1 block">查询</label>
                      <Textarea
                        value={ragQuery}
                        onChange={(e) => setRagQuery(e.target.value)}
                        placeholder="输入查询内容..."
                        rows={3}
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <label className="text-sm font-medium mb-1 block">返回数量</label>
                        <Input
                          type="number"
                          value={ragTopK}
                          onChange={(e) => setRagTopK(parseInt(e.target.value) || 3)}
                          min={1}
                          max={10}
                        />
                      </div>
                      <div className="flex-1">
                        <label className="text-sm font-medium mb-1 block">提供商</label>
                        <Select value={ragProvider} onValueChange={setRagProvider}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="qdrant">Qdrant</SelectItem>
                            <SelectItem value="milvus">Milvus</SelectItem>
                            <SelectItem value="weaviate">Weaviate</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Button onClick={handleRagSearch} disabled={ragLoading} className="w-full">
                      {ragLoading ? "检索中..." : "检索"}
                    </Button>
                    {ragError && <div className="text-sm text-red-600">{ragError}</div>}
                    {ragResults.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">
                          检索结果 ({ragResults.length} 条)
                          {ragProviderUsed && (
                            <span className="text-xs text-slate-500 ml-2">
                              使用: {ragProviderUsed}
                            </span>
                          )}
                        </h4>
                        {ragResults.map((r, idx) => (
                          <div key={idx} className="p-3 border rounded text-sm">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">文档: {r.document_id}</span>
                              <Badge variant="secondary" className="text-xs">
                                相似度: {(r.score * 100).toFixed(1)}%
                              </Badge>
                            </div>
                            <div className="text-slate-600 dark:text-slate-400 line-clamp-3">
                              {r.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* 其他工具内容 */}
            <TabsContent value="smartdoc" className="m-0 flex-1 overflow-hidden">
              <SmartDocPanelV3
                onExtractedContent={(content, title) => {
                  const message = title
                    ? `我提取了网页内容："${title}"\n\n${content}`
                    : content;
                  sendMessage(message);
                  onClose();
                }}
                onClose={onClose}
              />
            </TabsContent>
            <TabsContent value="trae-agent" className="m-0 flex-1 overflow-hidden">
              <TraeAgentPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="deerflow" className="m-0 flex-1 overflow-hidden">
              <DeerFlowPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="onyx" className="m-0 flex-1 overflow-hidden">
              <OnyxPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="bbbrowser" className="m-0 flex-1 overflow-hidden">
              <BBBrowserPanel />
            </TabsContent>
            <TabsContent value="webaccess" className="m-0 flex-1 overflow-hidden">
              <WebAccessPanel />
            </TabsContent>
            <TabsContent value="opencli" className="m-0 flex-1 overflow-hidden">
              <OpenCLIPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="openkb" className="m-0 flex-1 overflow-hidden">
              <OpenKBPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="graphify" className="m-0 flex-1 overflow-hidden">
              <GraphifyPanel />
            </TabsContent>
            <TabsContent value="llamaindex" className="m-0 flex-1 overflow-hidden">
              <LlamaIndexPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="forensic" className="m-0 flex-1 overflow-hidden">
              <ForensicAnalysisPanel onClose={onClose} />
            </TabsContent>
            <TabsContent value="batch-forensic" className="m-0 flex-1 overflow-hidden">
              <BatchForensicAnalysisPanel onClose={onClose} />
            </TabsContent>
            {Object.entries(tools).map(([id, tool]) => (
              <TabsContent key={id} value={id} className="m-0 flex-1 overflow-hidden">
                {renderToolContent()}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </CardContent>
    </Card>
  );
}
