"use client";

/**
 * Hyper-Extract Knowledge Extraction Page
 * 知识提取页面 - 集成 Hyper-Extract 框架
 * 
 * Features:
 * - Knowledge Graph extraction
 * - Hypergraph extraction (multi-entity relationships)
 * - Temporal extraction
 * - Spatial extraction
 * - Domain-specific templates
 */

import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Button from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { apiUrl } from "@/lib/api";
import {
  Brain,
  Search,
  Network,
  Clock,
  MapPin,
  Sparkles,
  Loader2,
  FileText,
  RefreshCw,
  Download,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Circle,
  Square,
  Hexagon,
} from "lucide-react";

// 输出类型
type OutputType = "graph" | "hypergraph" | "temporal" | "spatial" | "all";

// 模板类型
type TemplateType = "general" | "finance" | "legal" | "medical" | "tcm" | "industry";

// 实体类型
interface Entity {
  id: string;
  label: string;
  attributes?: Record<string, any>;
}

// 关系类型
interface Relation {
  source: string;
  relation: string;
  target: string;
}

// 超边类型
interface Hyperedge {
  id: string;
  entities: string[];
  relation: string;
  attributes?: Record<string, any>;
}

// 事件类型
interface Event {
  id: string;
  timestamp: string;
  description: string;
  entities: string[];
}

// 位置类型
interface Location {
  id: string;
  name: string;
  coordinates?: [number, number];
  type?: string;
}

// 提取结果类型
interface ExtractResult {
  success: boolean;
  type?: string;
  entities?: Entity[];
  relations?: Relation[];
  hyperedges?: Hyperedge[];
  events?: Event[];
  time_intervals?: { start: string; end: string; label: string }[];
  locations?: Location[];
  spatial_relations?: Relation[];
  summary?: string;
  knowledge_graph?: {
    entities: Entity[];
    relations: Relation[];
  };
  hypergraph?: {
    entities: Entity[];
    hyperedges: Hyperedge[];
  };
  temporal?: {
    events: Event[];
    time_intervals: { start: string; end: string; label: string }[];
  };
  spatial?: {
    locations: Location[];
    spatial_relations: Relation[];
  };
  error?: string;
}

// 模板配置
const TEMPLATES: { value: TemplateType; label: string; description: string }[] = [
  { value: "general", label: "通用", description: "适用于通用文本" },
  { value: "finance", label: "金融", description: "财务报表、股票分析" },
  { value: "legal", label: "法律", description: "合同、法条、判决书" },
  { value: "medical", label: "医疗", description: "病历、药品、手术记录" },
  { value: "tcm", label: "中医", description: "中药方剂、穴位、疗法" },
  { value: "industry", label: "工业", description: "技术文档、产品说明" },
];

// 输出类型配置
const OUTPUT_TYPES: { value: OutputType; label: string; icon: typeof Network }[] = [
  { value: "graph", label: "知识图谱", icon: Network },
  { value: "hypergraph", label: "超图", icon: Hexagon },
  { value: "temporal", label: "时间关系", icon: Clock },
  { value: "spatial", label: "空间关系", icon: MapPin },
  { value: "all", label: "全部提取", icon: Sparkles },
];

export default function KnowledgeExtractionPage() {
  const [inputText, setInputText] = useState<string>("");
  const [template, setTemplate] = useState<TemplateType>("general");
  const [outputType, setOutputType] = useState<OutputType>("all");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["graph"]));

  // 切换展开/折叠
  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  }, []);

  // 复制结果
  const copyResult = useCallback(async () => {
    if (result) {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("结果已复制到剪贴板");
    }
  }, [result]);

  // 下载结果
  const downloadResult = useCallback(() => {
    if (result) {
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `knowledge_extraction_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("结果已下载");
    }
  }, [result]);

  // 提取知识
  const extractKnowledge = useCallback(async () => {
    if (!inputText.trim()) {
      toast.error("请输入要提取的文本");
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch(apiUrl("/api/knowledge/extract"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: inputText,
          template,
          output_type: outputType,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setResult(data.data);
        // 展开所有相关部分
        const sections = new Set<string>();
        if (outputType === "all" || outputType === "graph") sections.add("graph");
        if (outputType === "all" || outputType === "hypergraph") sections.add("hypergraph");
        if (outputType === "all" || outputType === "temporal") sections.add("temporal");
        if (outputType === "all" || outputType === "spatial") sections.add("spatial");
        setExpandedSections(sections);
        toast.success("知识提取成功");
      } else {
        toast.error(data.error || "提取失败");
      }
    } catch (error) {
      console.error("提取失败:", error);
      toast.error("提取失败，请检查网络连接或服务状态");
    } finally {
      setIsLoading(false);
    }
  }, [inputText, template, outputType]);

  // 示例文本
  const loadExample = useCallback((example: string) => {
    setInputText(example);
  }, []);

  const examples = [
    "苹果公司于2023年9月在加州发布了iPhone 15，由CEO蒂姆·库克主持发布会。这款手机搭载了A17 Pro芯片，支持USB-C接口。",
    "阿里巴巴集团由马云于1999年创立，总部位于中国杭州，2023年营收超过8000亿元人民币。",
    "2024年1月15日，特斯拉宣布在上海超级工厂开始量产Model Y改款车型，预计年产能将达到75万辆。",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">知识提取</h1>
              <p className="text-slate-500 dark:text-slate-400">使用 Hyper-Extract 从文本中提取结构化知识</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：输入区域 */}
          <div className="space-y-6">
            {/* 输入卡片 */}
            <Card className="shadow-lg border-0">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  输入文本
                </CardTitle>
                <CardDescription>输入要提取知识的文本内容</CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="请输入要提取知识的文本...\n\n例如：苹果公司于2023年9月在加州发布了iPhone 15..."
                  className="h-48 resize-none font-mono text-sm"
                />
                
                {/* 示例按钮 */}
                <div className="mt-3">
                  <p className="text-sm text-slate-500 mb-2">快速示例：</p>
                  <div className="flex flex-wrap gap-2">
                    {examples.map((example, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => loadExample(example)}
                        className="text-xs"
                      >
                        示例 {index + 1}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 配置卡片 */}
            <Card className="shadow-lg border-0">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <SettingsIcon className="w-5 h-5 text-purple-500" />
                  提取配置
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 模板选择 */}
                <div>
                  <Label htmlFor="template" className="mb-2 block">领域模板</Label>
                  <Select value={template} onValueChange={(v) => setTemplate(v as TemplateType)}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="选择模板" />
                    </SelectTrigger>
                    <SelectContent>
                      {TEMPLATES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* 输出类型选择 */}
                <div>
                  <Label className="mb-2 block">输出类型</Label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {OUTPUT_TYPES.map((type) => {
                      const IconComponent = type.icon;
                      return (
                        <Button
                          key={type.value}
                          variant={outputType === type.value ? "default" : "outline"}
                          onClick={() => setOutputType(type.value)}
                          className="justify-start gap-2"
                        >
                          <IconComponent className="w-4 h-4" />
                          {type.label}
                        </Button>
                      );
                    })}
                  </div>
                </div>

                {/* 提取按钮 */}
                <Button
                  onClick={extractKnowledge}
                  disabled={isLoading || !inputText.trim()}
                  className="w-full h-12 text-lg"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      提取中...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5 mr-2" />
                      开始提取
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* 右侧：结果区域 */}
          <div className="space-y-6">
            {/* 结果卡片 */}
            <Card className="shadow-lg border-0">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-500" />
                    提取结果
                  </CardTitle>
                  {result && (
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={copyResult}>
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                      <Button variant="outline" size="sm" onClick={downloadResult}>
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                      <p className="text-slate-500">正在提取知识...</p>
                    </div>
                  </div>
                ) : result ? (
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {/* 摘要 */}
                    {result.summary && (
                      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                        <p className="text-sm text-amber-800 dark:text-amber-200">{result.summary}</p>
                      </div>
                    )}

                    {/* 知识图谱 */}
                    {(result.type === "knowledge_graph" || result.knowledge_graph || outputType === "all") && (
                      <div className="border rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection("graph")}
                          className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Network className="w-4 h-4 text-blue-500" />
                            <span className="font-medium">知识图谱</span>
                            {result.entities && (
                              <Badge variant="secondary">{result.entities.length} 实体</Badge>
                            )}
                            {result.relations && (
                              <Badge variant="secondary">{result.relations.length} 关系</Badge>
                            )}
                          </div>
                          {expandedSections.has("graph") ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                        {expandedSections.has("graph") && (
                          <div className="p-4 space-y-4">
                            {/* 实体列表 */}
                            {(result.entities || result.knowledge_graph?.entities) && (
                              <div>
                                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">实体</h4>
                                <div className="flex flex-wrap gap-2">
                                  {(result.entities || result.knowledge_graph?.entities).map((entity: Entity) => (
                                    <Badge key={entity.id} className="gap-1">
                                      <Circle className="w-2 h-2 text-green-500" />
                                      {entity.label}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 关系列表 */}
                            {(result.relations || result.knowledge_graph?.relations) && (
                              <div>
                                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">关系</h4>
                                <div className="space-y-2">
                                  {(result.relations || result.knowledge_graph?.relations).map((rel: Relation, idx) => (
                                    <div key={idx} className="flex items-center gap-2 text-sm p-2 bg-slate-50 dark:bg-slate-800 rounded">
                                      <span className="text-slate-600 dark:text-slate-400">{rel.source}</span>
                                      <span className="text-blue-500 font-medium">→</span>
                                      <Badge variant="outline">{rel.relation}</Badge>
                                      <span className="text-slate-600 dark:text-slate-400">→</span>
                                      <span className="text-slate-600 dark:text-slate-400">{rel.target}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 超图 */}
                    {(result.type === "hypergraph" || result.hypergraph || outputType === "all") && (
                      <div className="border rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection("hypergraph")}
                          className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Hexagon className="w-4 h-4 text-purple-500" />
                            <span className="font-medium">超图</span>
                            {result.hyperedges && (
                              <Badge variant="secondary">{result.hyperedges.length} 超边</Badge>
                            )}
                          </div>
                          {expandedSections.has("hypergraph") ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                        {expandedSections.has("hypergraph") && (
                          <div className="p-4 space-y-4">
                            {/* 超边列表 */}
                            {(result.hyperedges || result.hypergraph?.hyperedges) && (
                              <div>
                                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">超边（多实体关系）</h4>
                                <div className="space-y-2">
                                  {(result.hyperedges || result.hypergraph?.hyperedges).map((he: Hyperedge, idx) => (
                                    <div key={idx} className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                                      <div className="flex flex-wrap gap-2 mb-2">
                                        {he.entities.map((e, i) => (
                                          <Badge key={i} variant="secondary">{e}</Badge>
                                        ))}
                                      </div>
                                      <div className="text-sm text-purple-700 dark:text-purple-300">
                                        关系：<strong>{he.relation}</strong>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 时间关系 */}
                    {(result.type === "temporal" || result.temporal || outputType === "all") && (
                      <div className="border rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection("temporal")}
                          className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-green-500" />
                            <span className="font-medium">时间关系</span>
                            {result.events && (
                              <Badge variant="secondary">{result.events.length} 事件</Badge>
                            )}
                          </div>
                          {expandedSections.has("temporal") ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                        {expandedSections.has("temporal") && (
                          <div className="p-4 space-y-4">
                            {/* 事件列表 */}
                            {(result.events || result.temporal?.events) && (
                              <div>
                                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">事件</h4>
                                <div className="space-y-2">
                                  {(result.events || result.temporal?.events).map((event: Event, idx) => (
                                    <div key={idx} className="flex items-start gap-3 p-2 bg-green-50 dark:bg-green-900/20 rounded">
                                      <Badge variant="outline" className="shrink-0">{event.timestamp}</Badge>
                                      <div>
                                        <p className="text-sm">{event.description}</p>
                                        {event.entities.length > 0 && (
                                          <div className="flex flex-wrap gap-1 mt-1">
                                            {event.entities.map((e, i) => (
                                              <span key={i} className="text-xs text-green-600 dark:text-green-400">{e}</span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 空间关系 */}
                    {(result.type === "spatial" || result.spatial || outputType === "all") && (
                      <div className="border rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection("spatial")}
                          className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4 text-red-500" />
                            <span className="font-medium">空间关系</span>
                            {result.locations && (
                              <Badge variant="secondary">{result.locations.length} 位置</Badge>
                            )}
                          </div>
                          {expandedSections.has("spatial") ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                        {expandedSections.has("spatial") && (
                          <div className="p-4 space-y-4">
                            {/* 位置列表 */}
                            {(result.locations || result.spatial?.locations) && (
                              <div>
                                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">位置</h4>
                                <div className="flex flex-wrap gap-2">
                                  {(result.locations || result.spatial?.locations).map((loc: Location, idx) => (
                                    <Badge key={idx} className="gap-1 bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20">
                                      <MapPin className="w-3 h-3" />
                                      {loc.name}
                                      {loc.type && `(${loc.type})`}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 text-slate-400">
                    <div className="text-center">
                      <Brain className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                      <p>输入文本并点击「开始提取」按钮</p>
                      <p className="text-sm mt-2">支持知识图谱、超图、时空关系提取</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 功能说明 */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                  <Network className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white">知识图谱</h3>
                  <p className="text-sm text-slate-500">识别实体和二元关系，生成三元组</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0">
                  <Hexagon className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white">超图提取</h3>
                  <p className="text-sm text-slate-500">处理多实体复杂关系，Hyper-Extract 核心优势</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white">时间关系</h3>
                  <p className="text-sm text-slate-500">自动识别时间戳和时间间隔</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center shrink-0">
                  <MapPin className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white">空间关系</h3>
                  <p className="text-sm text-slate-500">提取地理位置和空间关系</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// 临时设置图标组件
function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}