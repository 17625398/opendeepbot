"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import Link from "next/link";
import {
  Send,
  Bot,
  User,
  Settings,
  Terminal,
  MessageSquare,
  TrendingUp,
  HardDrive,
  ChevronDown,
  RefreshCw,
  Square,
  Play,
  CheckCircle,
  PauseCircle,
  Link2,
  Plus,
  X,
} from "lucide-react";
import Button from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

// 消息类型
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  metadata?: {
    cost?: number;
    tokens?: number;
    channel?: string;
    toolCalls?: Array<any>;
    thinking?: string;
  };
}

// 通道状态
interface ChannelStatus {
  name: string;
  enabled: boolean;
  connected: boolean;
  status: string;
}

// 加载状态组件
function LoadingState() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-600 dark:text-slate-400">Loading...</span>
      </div>
    </div>
  );
}

// 主内容组件
function DeepTutorChatContent() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "你好！我是 DeepTutor，一个多平台 AI 助手。我可以通过 Telegram、Discord、WeChat、Email 等多个平台与你交流。\n\n有什么我可以帮助你的吗？",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [yoloMode, setYoloMode] = useState(false);
  const [costTracking, setCostTracking] = useState(true);
  const [totalCost, setTotalCost] = useState(0);
  const [activeTab, setActiveTab] = useState("chat");
  const [isMounted, setIsMounted] = useState(false);

  // 通道状态
  const [channels, setChannels] = useState<ChannelStatus[]>([
    { name: "WebSocket", enabled: true, connected: true, status: "在线" },
    { name: "Telegram", enabled: false, connected: false, status: "未配置" },
    { name: "Discord", enabled: false, connected: false, status: "未配置" },
    { name: "WeChat", enabled: false, connected: false, status: "未配置" },
    { name: "Slack", enabled: false, connected: false, status: "未配置" },
    { name: "Email", enabled: false, connected: false, status: "未配置" },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // 防止 hydration 不匹配
  if (!isMounted) {
    return null;
  }

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    // 模拟 AI 回复
    setTimeout(() => {
      const responses = [
        "好的，让我来帮你处理这个问题...",
        "这是一个有趣的想法！让我深入思考一下...",
        "我理解你的需求了。让我为你提供最佳方案...",
        "感谢你的提问！我来为你详细分析...",
      ];

      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      const randomCost = Math.random() * 0.01;

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `${randomResponse}\n\n**分析过程**：\n我正在思考这个问题的最佳解决方案，同时会考虑成本和效率因素。\n\n**建议**：\n你可以尝试以下步骤来解决这个问题...`,
        timestamp: new Date(),
        metadata: {
          cost: randomCost,
          tokens: Math.floor(Math.random() * 500 + 100),
          channel: "Web UI",
          thinking: "思考过程正在进行中...",
        },
      };

      setMessages((prev) => [...prev, aiMessage]);
      setTotalCost((prev) => prev + randomCost);
      setIsLoading(false);
    }, 1500);
  };

  // 模拟启动通道
  const toggleChannel = (channelName: string) => {
    setChannels((prev) =>
      prev.map((channel) => {
        if (channel.name === channelName) {
          const newEnabled = !channel.enabled;
          return {
            ...channel,
            enabled: newEnabled,
            connected: newEnabled,
            status: newEnabled ? "已连接" : "未配置",
          };
        }
        return channel;
      })
    );
  };

  // 清除聊天记录
  const clearChat = () => {
    if (confirm("确定要清除所有聊天记录吗？")) {
      setMessages([]);
      setTotalCost(0);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 p-4">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-2rem)]">
        {/* 左侧面板 - 通道管理 */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-blue-600" />
                通道管理
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {channels.map((channel) => (
                <div
                  key={channel.name}
                  className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                    channel.enabled ? "bg-blue-50 dark:bg-blue-900/20" : "bg-white dark:bg-slate-800/50"
                  } hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer`}
                  onClick={() => toggleChannel(channel.name)}
                >
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Avatar className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 text-white">
                        {channel.name.charAt(0)}
                      </Avatar>
                      <div
                        className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-slate-900 ${
                          channel.connected ? "bg-emerald-500" : "bg-slate-400"
                        }`}
                      />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{channel.name}</div>
                      <div className={`text-xs ${
                        channel.enabled ? "text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-slate-400"
                      }`}>
                        {channel.status}
                      </div>
                    </div>
                  </div>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="w-8 h-8">
                          {channel.enabled ? <Square className="w-4 h-4 text-red-500" /> : <Play className="w-4 h-4 text-emerald-500" />}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        {channel.enabled ? "关闭通道" : "启动通道"}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* 成本统计 */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                成本统计
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-4">
                <div className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
                  ${totalCost.toFixed(4)}
                </div>
                <div className="text-sm text-slate-500 dark:text-slate-400">总成本</div>
              </div>
              <div className="flex justify-center">
                <Badge variant="outline" className="flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  {messages.length} 条消息
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* 系统设置 */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-purple-600" />
                设置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">YOLO 模式（自动执行）</span>
                <Badge
                  variant={yoloMode ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setYoloMode(!yoloMode)}
                >
                  {yoloMode ? "开启" : "关闭"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">成本追踪</span>
                <Badge
                  variant={costTracking ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setCostTracking(!costTracking)}
                >
                  {costTracking ? "开启" : "关闭"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 中间面板 - 聊天 */}
        <div className="lg:col-span-6 flex flex-col">
          <Card className="flex-1 flex flex-col border-0 shadow-lg overflow-hidden">
            {/* 聊天头部 */}
            <CardHeader className="flex-row items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <Avatar className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500">
                  <Bot className="w-5 h-5 text-white" />
                </Avatar>
                <div>
                  <CardTitle className="text-lg">DeepTutor</CardTitle>
                  <p className="text-sm text-slate-500 dark:text-slate-400">多平台 AI 助手</p>
                </div>
                {yoloMode && (
                  <Badge className="bg-emerald-500 hover:bg-emerald-600">YOLO 模式</Badge>
                )}
              </div>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" onClick={clearChat}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>清除聊天</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </CardHeader>

            {/* 消息列表 */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                  <Bot className="w-16 h-16 text-slate-400" />
                  <div>
                    <h3 className="text-lg font-medium">开始你的对话</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      选择左侧的通道，或直接在下方发送消息
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-2xl ${
                        message.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar className="w-6 h-6">
                          {message.role === "user" ? (
                            <User className="w-3 h-3" />
                          ) : (
                            <Bot className="w-3 h-3" />
                          )}
                        </Avatar>
                        <span className="text-xs opacity-70">
                          {message.role === "user" ? "你" : "DeepTutor"} · {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="whitespace-pre-wrap text-sm">{message.content}</div>

                      {/* 消息元数据 */}
                      {message.metadata && (
                        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700 space-y-2">
                          <div className="flex flex-wrap gap-2">
                            {message.metadata.channel && (
                              <Badge variant="outline" className="flex items-center gap-1">
                                <Link2 className="w-3 h-3" />
                                {message.metadata.channel}
                              </Badge>
                            )}
                            {message.metadata.tokens && (
                              <Badge variant="outline">{message.metadata.tokens} tokens</Badge>
                            )}
                            {message.metadata.cost && (
                              <Badge variant="outline" className="text-emerald-600 border-emerald-200">
                                ${message.metadata.cost.toFixed(4)}
                              </Badge>
                            )}
                          </div>

                          {/* 思考过程 */}
                          {message.metadata.thinking && (
                            <Accordion type="single" collapsible className="w-full">
                              <AccordionItem value="thinking">
                                <AccordionTrigger className="py-2 text-xs">思考过程</AccordionTrigger>
                                <AccordionContent>
                                  <p className="text-xs text-slate-500 dark:text-slate-400">
                                    {message.metadata.thinking}
                                  </p>
                                </AccordionContent>
                              </AccordionItem>
                            </Accordion>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700">
                    <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </CardContent>

            {/* 输入区域 */}
            <CardContent className="border-t border-slate-200 dark:border-slate-800 p-4">
              <div className="flex gap-3">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="输入消息..."
                  className="flex-1"
                  disabled={isLoading}
                />
                <Button onClick={handleSendMessage} disabled={!inputText.trim() || isLoading}>
                  <Send className="w-4 h-4 mr-2" />
                  发送
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右侧面板 - 工具和信息 */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-cyan-600" />
                系统状态
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium">DeepTutor 后端</span>
                </div>
                <span className="text-sm text-emerald-600">运行中</span>
              </div>

              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">已配置通道</span>
                  <span className="font-medium">
                    {channels.filter((c) => c.enabled).length}/{channels.length}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">WebSocket 服务</span>
                  <span className="font-medium text-emerald-600">端口 8765</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">API 服务</span>
                  <span className="font-medium text-emerald-600">端口 8001</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 快速帮助 */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-amber-600" />
                快速使用
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="text-sm font-medium">📱 Telegram</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">在 .env 中配置 TELEGRAM_TOKEN</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">🎮 Discord</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">在 .env 中配置 DISCORD_TOKEN</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">🔌 WebSocket</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">ws://localhost:8765</div>
              </div>
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                <Link href="/dashboard">
                  <Button variant="outline" className="w-full gap-2">
                    <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
                    返回仪表板
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// 主页面组件
export default function DeepTutorChatPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <DeepTutorChatContent />
    </Suspense>
  );
}
