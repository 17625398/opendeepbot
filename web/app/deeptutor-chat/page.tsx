'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  CircularProgress,
  Chip,
  Stack,
  Divider,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
  Badge,
  IconButton,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  Settings,
  Terminal,
  ChatBubble,
  TrendingUp,
  Storage,
  ExpandMore,
  Refresh,
  Stop,
  PlayArrow,
  CheckCircle,
  PauseCircle,
  Webhook,
} from '@mui/icons-material';

// 消息类型
interface Message {
  id: string;
  role: 'user' | 'assistant';
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

export default function DeepTutorChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '你好！我是 DeepTutor，一个多平台 AI 助手。我可以通过 Telegram、Discord、WeChat、Email 等多个平台与你交流。\n\n有什么我可以帮助你的吗？',
      timestamp: new Date(),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [yoloMode, setYoloMode] = useState(false);
  const [costTracking, setCostTracking] = useState(true);
  const [totalCost, setTotalCost] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  
  // 通道状态
  const [channels, setChannels] = useState<ChannelStatus[]>([
    { name: 'WebSocket', enabled: true, connected: true, status: '在线' },
    { name: 'Telegram', enabled: false, connected: false, status: '未配置' },
    { name: 'Discord', enabled: false, connected: false, status: '未配置' },
    { name: 'WeChat', enabled: false, connected: false, status: '未配置' },
    { name: 'Slack', enabled: false, connected: false, status: '未配置' },
    { name: 'Email', enabled: false, connected: false, status: '未配置' },
  ]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // 模拟 AI 回复
    setTimeout(() => {
      const responses = [
        "好的，让我来帮您处理这个问题...",
        "这是一个有趣的想法！让我深入思考一下...",
        "我理解您的需求了。让我为您提供最佳方案...",
        "感谢您的提问！我来为您详细分析...",
      ];
      
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      const randomCost = Math.random() * 0.01;
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `${randomResponse}\n\n**分析过程**：\n我正在思考这个问题的最佳解决方案，同时会考虑成本和效率因素。\n\n**建议**：\n您可以尝试以下步骤来解决这个问题...`,
        timestamp: new Date(),
        metadata: {
          cost: randomCost,
          tokens: Math.floor(Math.random() * 500 + 100),
          channel: 'Web UI',
          thinking: '思考过程正在进行中...',
        }
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setTotalCost(prev => prev + randomCost);
      setIsLoading(false);
    }, 1500);
  };

  // 模拟启动通道
  const toggleChannel = (channelName: string) => {
    setChannels(prev => prev.map(channel => {
      if (channel.name === channelName) {
        const newEnabled = !channel.enabled;
        return {
          ...channel,
          enabled: newEnabled,
          connected: newEnabled,
          status: newEnabled ? '已连接' : '未配置',
        };
      }
      return channel;
    }));
  };

  // 清除聊天记录
  const clearChat = () => {
    if (confirm('确定要清除所有聊天记录吗？')) {
      setMessages([]);
      setTotalCost(0);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ height: '100vh', py: 2 }}>
      <Stack direction="row" spacing={2} sx={{ height: '100%' }}>
        {/* 左侧面板 - 通道管理 */}
        <Box sx={{ width: 280, flexShrink: 0 }}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Storage sx={{ color: 'primary.main' }} />
                通道管理
              </Typography>
              <List dense>
                {channels.map(channel => (
                  <ListItem
                    key={channel.name}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      bgcolor: channel.enabled ? 'action.selected' : 'transparent',
                    }}
                    secondaryAction={
                      <Tooltip title={channel.enabled ? '关闭通道' : '启动通道'}>
                        <IconButton
                          size="small"
                          onClick={() => toggleChannel(channel.name)}
                        >
                          {channel.enabled ? <Stop fontSize="small" color="error" /> : <PlayArrow fontSize="small" color="success" />}
                        </IconButton>
                      </Tooltip>
                    }
                  >
                    <ListItemAvatar>
                      <Badge
                        overlap="circular"
                        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                        variant="dot"
                        color={channel.connected ? 'success' : 'default'}
                      >
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {channel.name.charAt(0)}
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>
                    <ListItemText
                      primary={channel.name}
                      secondary={
                        <Typography variant="caption" color={channel.enabled ? 'success.main' : 'text.secondary'}>
                          {channel.status}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* 成本统计 */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp sx={{ color: 'success.main' }} />
                成本统计
              </Typography>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  ${totalCost.toFixed(4)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  总成本
                </Typography>
              </Box>
              <Stack direction="row" spacing={1} sx={{ mt: 2, justifyContent: 'center' }}>
                <Chip
                  icon={<CheckCircle fontSize="small" />}
                  label={`${messages.length} 条消息`}
                  size="small"
                  variant="outlined"
                />
              </Stack>
            </CardContent>
          </Card>

          {/* 系统设置 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings sx={{ color: 'secondary.main' }} />
                设置
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">YOLO 模式（自动执行）</Typography>
                  <Chip
                    size="small"
                    label={yoloMode ? '开启' : '关闭'}
                    color={yoloMode ? 'success' : 'default'}
                    onClick={() => setYoloMode(!yoloMode)}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">成本追踪</Typography>
                  <Chip
                    size="small"
                    label={costTracking ? '开启' : '关闭'}
                    color={costTracking ? 'primary' : 'default'}
                    onClick={() => setCostTracking(!costTracking)}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Box>

        {/* 中间面板 - 聊天 */}
        <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* 聊天头部 */}
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SmartToy />
                </Avatar>
                <Box>
                  <Typography variant="h6">DeepTutor</Typography>
                  <Typography variant="caption" color="text.secondary">
                    多平台 AI 助手
                  </Typography>
                </Box>
                {yoloMode && (
                  <Chip label="YOLO 模式" color="success" size="small" />
                )}
              </Box>
              <IconButton onClick={clearChat} size="small">
                <Refresh />
              </IconButton>
            </Stack>
          </Box>

          {/* 消息列表 */}
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
            {messages.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h5" color="text.secondary" gutterBottom>
                  开始你的对话
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  选择左侧的通道，或直接在下方发送消息
                </Typography>
              </Box>
            ) : (
              <Stack spacing={2}>
                {messages.map(message => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <Paper
                      sx={{
                        p: 2,
                        maxWidth: '70%',
                        bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                        color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                      }}
                    >
                      <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 1 }}>
                        <Avatar sx={{ width: 24, height: 24 }}>
                          {message.role === 'user' ? <Person fontSize="small" /> : <SmartToy fontSize="small" />}
                        </Avatar>
                        <Typography variant="caption" color="text.secondary">
                          {message.role === 'user' ? '你' : 'DeepTutor'} · {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Stack>
                      <Typography sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                      
                      {/* 消息元数据 */}
                      {message.metadata && (
                        <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                          <Stack direction="row" spacing={1} flexWrap="wrap">
                            {message.metadata.channel && (
                              <Chip size="small" icon={<Webhook />} label={message.metadata.channel} variant="outlined" />
                            )}
                            {message.metadata.tokens && (
                              <Chip size="small" label={`${message.metadata.tokens} tokens`} variant="outlined" />
                            )}
                            {message.metadata.cost && (
                              <Chip size="small" label={`$${message.metadata.cost.toFixed(4)}`} color="success" variant="outlined" />
                            )}
                          </Stack>
                          
                          {/* 思考过程 */}
                          {message.metadata.thinking && (
                            <Accordion sx={{ mt: 1 }}>
                              <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="caption">思考过程</Typography>
                              </AccordionSummary>
                              <AccordionDetails>
                                <Typography variant="body2" color="text.secondary">
                                  {message.metadata.thinking}
                                </Typography>
                              </AccordionDetails>
                            </Accordion>
                          )}
                        </Box>
                      )}
                    </Paper>
                  </Box>
                ))}
                {isLoading && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <Paper sx={{ p: 2 }}>
                      <CircularProgress size={24} />
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Stack>
            )}
          </Box>

          {/* 输入区域 */}
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder="输入消息..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={isLoading}
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={!inputText.trim() || isLoading}
                endIcon={<Send />}
                sx={{ alignSelf: 'flex-end' }}
              >
                发送
              </Button>
            </Stack>
          </Box>
        </Paper>

        {/* 右侧面板 - 工具和信息 */}
        <Box sx={{ width: 320, flexShrink: 0 }}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Terminal sx={{ color: 'info.main' }} />
                系统状态
              </Typography>
              
              <Alert severity="success" sx={{ mb: 2 }}>
                ✅ DeepTutor 后端运行中
              </Alert>
              
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  已配置通道: {channels.filter(c => c.enabled).length}/{channels.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  WebSocket 服务: 端口 8765
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  API 服务: 端口 8001
                </Typography>
              </Stack>
            </CardContent>
          </Card>

          {/* 快速帮助 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ChatBubble sx={{ color: 'warning.main' }} />
                快速使用
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="📱 Telegram"
                    secondary="在 .env 中配置 TELEGRAM_TOKEN"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="🎮 Discord"
                    secondary="在 .env 中配置 DISCORD_TOKEN"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="🔌 WebSocket"
                    secondary="ws://localhost:8765"
                  />
                </ListItem>
              </List>
              <Divider sx={{ my: 1 }} />
              <Typography variant="caption" color="text.secondary">
                查看 QUICKSTART.md 了解完整使用说明
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Stack>
    </Container>
  );
}
