"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Layout, Input, Button, Card, Typography, Space, Tag, Spin, Dropdown, App } from "antd";
import type { MenuProps } from "antd";
import { SendOutlined, HeartFilled, ClockCircleOutlined, UserOutlined, LogoutOutlined } from "@ant-design/icons";

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

interface EmotionHistory {
  emotion_label: string;
  intensity: number;
  timestamp: string;
}

export default function Home() {
  const { message } = App.useApp();
  const router = useRouter();
  const [text, setText] = useState("");
  const [status, setStatus] = useState<"idle" | "analyzing" | "matching">("idle");
  const [emotion, setEmotion] = useState<{ label: string; intensity: number } | null>(null);
  const [clientId, setClientId] = useState("");
  const [username, setUsername] = useState<string | null>(null);
  const [history, setHistory] = useState<EmotionHistory[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUsername = localStorage.getItem("username");
    const storedUserId = localStorage.getItem("user_id");

    if (token && storedUsername && storedUserId) {
      setUsername(storedUsername);
      setClientId(storedUserId);
      fetchHistory(token);
    } else {
      setClientId(Math.random().toString(36).substring(2, 10));
    }
  }, []);

  const fetchHistory = async (token: string) => {
    const host = window.location.hostname;
    try {
      const res = await fetch(`http://${host}:8000/api/auth/history`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("user_id");
    setUsername(null);
    setHistory([]);
    setClientId(Math.random().toString(36).substring(2, 10));
    message.success("已退出登录");
  };

  const handleAnalyze = async () => {
    if (!username || !localStorage.getItem("token")) {
      message.warning("必须登录才能使用匿名共鸣空间哦！");
      router.push("/login");
      return;
    }
    
    if (!text.trim()) return;
    setStatus("analyzing");

    try {
      const host = window.location.hostname;
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // 1. Analyze Emotion
      const res = await fetch(`http://${host}:8000/api/emotion/analyze`, {
        method: "POST",
        headers,
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      setEmotion({ label: data.emotion_label, intensity: data.intensity_score });
      setStatus("matching");

      // 2. Request Match
      const matchRes = await fetch(`http://${host}:8000/api/ws/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: clientId,
          emotion_label: data.emotion_label,
          intensity: data.intensity_score,
          polarity: data.polarity,
          keywords: data.keywords || []
        }),
      });
      
      if (!matchRes.ok) {
        const errData = await matchRes.json();
        throw new Error(errData.detail || "Match request failed");
      }
      
      const matchData = await matchRes.json();
      
      // 3. Redirect to Room
      if (matchData.room_id) {
        router.push(`/chat/${matchData.room_id}?clientId=${clientId}`);
      }
    } catch (error) {
      console.error("Error:", error);
      setStatus("idle");
      message.error("连接服务器失败，请稍后重试。");
    }
  };

  const userMenu: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <Layout className="min-h-screen relative bg-[#f8fafc] overflow-hidden">
      {/* Dreamy Ambient Background */}
      <div className="absolute top-[-10%] left-[-5%] w-[600px] h-[600px] bg-[#e6fffb] rounded-full blur-[120px] opacity-70 pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[600px] h-[600px] bg-[#fff0f6] rounded-full blur-[120px] opacity-70 pointer-events-none z-0" />
      <div className="absolute top-[30%] left-[50%] w-[500px] h-[500px] bg-[#f0f5ff] rounded-full blur-[150px] opacity-50 pointer-events-none z-0 transform -translate-x-1/2" />

      {/* Header */}
      <Header 
        className="px-6 md:px-12 flex items-center justify-between sticky top-0 z-50 shadow-sm"
        style={{ 
          background: 'rgba(255, 255, 255, 0.85)', 
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(229, 231, 235, 0.5)'
        }}
      >
        <div className="flex items-center gap-3">
          <HeartFilled className="text-[#13c2c2] text-2xl" />
          <Title level={4} className="!m-0 tracking-tight text-slate-800">
            VibeChat
          </Title>
        </div>
        <div>
          {username ? (
            <Dropdown menu={{ items: userMenu }} placement="bottomRight">
              <Button type="text" className="flex items-center gap-2 hover:bg-black/5 text-slate-600 font-medium">
                <UserOutlined />
                {username}
              </Button>
            </Dropdown>
          ) : (
            <Button type="primary" onClick={() => router.push("/login")} className="shadow-md">
              登录 / 注册
            </Button>
          )}
        </div>
      </Header>

      <Content className="p-6 md:p-12 flex justify-center z-10 relative">
        <div className="w-full max-w-[800px] flex flex-col gap-8">
          {status === "idle" && (
            <>
              <Card 
                variant="borderless" 
                className="shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl bg-white/95 backdrop-blur-sm"
                title={
                  <Space className="py-2">
                    <HeartFilled className="text-[#13c2c2] text-lg" />
                    <span className="font-semibold text-slate-700 text-lg">记录此刻</span>
                  </Space>
                }
              >
                <TextArea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="我现在感觉..."
                  autoSize={{ minRows: 4, maxRows: 8 }}
                  className="mb-6 text-base p-4 bg-slate-50 border-slate-200 focus:bg-white rounded-xl shadow-inner transition-colors"
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault();
                      handleAnalyze();
                    }
                  }}
                />
                <div className="flex justify-end">
                  <Button 
                    type="primary" 
                    size="large"
                    icon={<SendOutlined />}
                    disabled={!text.trim()}
                    onClick={handleAnalyze}
                    className="px-8 rounded-xl shadow-md h-12 text-base font-medium"
                  >
                    感知情绪
                  </Button>
                </div>
              </Card>

              {username && history.length > 0 && (
                <Card 
                  variant="borderless" 
                  className="shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl bg-white/95 backdrop-blur-sm"
                  title={
                    <Space className="py-2">
                      <ClockCircleOutlined className="text-slate-500 text-lg" />
                      <span className="font-semibold text-slate-700 text-lg">情绪印记</span>
                    </Space>
                  }
                >
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                    {history.map((item, index) => (
                      <Card 
                        key={index}
                        size="small" 
                        variant="borderless"
                        className="bg-slate-50/80 border border-slate-100 rounded-xl hover:shadow-md transition-shadow"
                      >
                        <div className="text-xs text-slate-400 mb-3 font-medium">
                          {new Date(item.timestamp).toLocaleDateString()}
                        </div>
                        <div className="flex items-center justify-between">
                          <Text strong className="text-slate-700 text-base">{item.emotion_label}</Text>
                          <Tag color="cyan" className="rounded-md border-0 bg-cyan-50 text-cyan-600 font-medium">
                            强度 {item.intensity}
                          </Tag>
                        </div>
                      </Card>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}

          {status === "analyzing" && (
            <Card variant="borderless" className="shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl bg-white/95 backdrop-blur-sm py-20 text-center">
              <Spin size="large" />
              <Title level={3} className="!mt-8 !mb-3 text-slate-700">正在感知你的心声...</Title>
              <Text type="secondary" className="text-base">让情绪化作微风</Text>
            </Card>
          )}

          {status === "matching" && emotion && (
            <Card variant="borderless" className="shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl bg-white/95 backdrop-blur-sm p-10 text-center">
              <div className="flex flex-col gap-6 w-full">
                <div className="bg-slate-50 rounded-2xl p-8 mb-4">
                  <Text type="secondary" className="uppercase tracking-widest text-xs font-semibold">捕获到的情绪</Text>
                  <Title level={2} className="!mt-3 !mb-5 text-slate-800">{emotion.label}</Title>
                  <Tag color="cyan" className="px-4 py-1.5 text-sm rounded-lg border-0 bg-cyan-50 text-cyan-600 font-medium">
                    强度 {emotion.intensity}/10
                  </Tag>
                </div>
                
                <div className="py-8">
                  <Spin size="large" />
                  <Title level={4} className="!mt-8 !mb-3 text-slate-700">正在寻找共鸣...</Title>
                  <Text type="secondary" className="text-base">匹配同样【{emotion.label}】的灵魂</Text>
                </div>
              </div>
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}
