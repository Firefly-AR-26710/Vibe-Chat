"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Sparkles, ArrowLeft } from "lucide-react";
import { CustomModal } from "@/components/CustomModal";

interface Message {
  type: "system" | "message" | "identity";
  content?: string;
  sender?: string;
  id: string;
  color?: string;
  nickname?: string;
}

export default function ChatRoom() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const roomId = params.roomId as string;
  const clientId = searchParams.get("clientId");
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [myIdentity, setMyIdentity] = useState<{nickname: string, color: string} | null>(null);
  const [emotionState, setEmotionState] = useState<{
    emotion_label: string;
    intensity: number;
    polarity: string;
    suggestions: string[];
  } | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const mainRef = useRef<HTMLElement>(null);
  
  const [modalState, setModalState] = useState<{isOpen: boolean, content: string}>({ isOpen: false, content: "" });

  const isAiRoom = roomId?.startsWith("ai_room_");

  useEffect(() => {
    if (!roomId || !clientId) {
      router.push("/");
      return;
    }

    const host = window.location.hostname;
    // 如果前端是在 3000 端口运行（本地 npm run dev），则连接本地 8000 的 uvicorn
    // 否则（Docker部署的 3002 端口或生产环境），连接 8002
    const wsPort = window.location.port === "3000" ? "8000" : "8002";
    const socket = new WebSocket(`ws://${host}:${wsPort}/api/ws/chat/${roomId}/${clientId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "identity") {
        setMyIdentity({ nickname: data.nickname, color: data.color });
      } else if (data.type === "emotion_state") {
        setEmotionState({
          emotion_label: data.emotion_label,
          intensity: data.intensity,
          polarity: data.polarity,
          suggestions: data.suggestions
        });
      } else if (data.type === "error") {
        setModalState({ isOpen: true, content: data.content });
      } else {
        setMessages((prev) => [...prev, { ...data, id: Math.random().toString() }]);
      }
    };

    socket.onclose = () => {
      setMessages((prev) => [...prev, { type: "system", content: "微风中断了连接...", sender: "system", id: Math.random().toString() }]);
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [roomId, clientId, router]);

  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTo({
        top: mainRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages]);

  const sendMessage = () => {
    if (ws && input.trim()) {
      ws.send(input);
      setInput("");
      setShowSuggestions(false);
    }
  };

  const getBubbleStyle = (isMe: boolean) => {
    if (!isMe) return "bg-white text-slate-700 border-slate-100 rounded-2xl rounded-tl-sm";
    
    if (emotionState?.polarity === "积极") return "bg-amber-500 text-white border-amber-500 rounded-2xl rounded-tr-sm";
    if (emotionState?.polarity === "消极") return "bg-indigo-500 text-white border-indigo-500 rounded-2xl rounded-tr-sm";
    return "bg-[#13c2c2] text-white border-[#13c2c2] rounded-2xl rounded-tr-sm";
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-[#f8fafc] font-sans text-slate-800 relative overflow-hidden">
      <CustomModal 
        isOpen={modalState.isOpen} 
        onClose={() => setModalState({ ...modalState, isOpen: false })} 
        title="提示" 
        content={modalState.content} 
      />
      {/* Dreamy Ambient Background (matching homepage) */}
      <div className="absolute top-[-10%] left-[-5%] w-[600px] h-[600px] bg-[#e6fffb] rounded-full blur-[120px] opacity-70 pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[600px] h-[600px] bg-[#fff0f6] rounded-full blur-[120px] opacity-70 pointer-events-none z-0" />
      <div className="absolute top-[30%] left-[50%] w-[500px] h-[500px] bg-[#f0f5ff] rounded-full blur-[150px] opacity-50 pointer-events-none z-0 transform -translate-x-1/2" />

      {/* Header */}
      <header 
        className="flex items-center justify-between px-6 py-4 z-10 shadow-sm shrink-0"
        style={{ 
          background: 'rgba(255, 255, 255, 0.85)', 
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(229, 231, 235, 0.5)'
        }}
      >
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/")} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500 hover:text-slate-800">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex flex-col">
            <h1 className="font-semibold text-lg flex items-center gap-2 text-slate-800">
              匿名共鸣空间
              {isAiRoom && <span className="bg-rose-50 text-rose-500 text-xs px-2.5 py-0.5 rounded-md border border-rose-100 ml-2 shadow-sm font-medium">AI 伴侣</span>}
            </h1>
            <span className="text-xs text-slate-500">
              {myIdentity ? `你是：${myIdentity.nickname}` : "微风正在连接..."}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
           <div className={`w-2 h-2 rounded-full animate-pulse ${ws?.readyState === WebSocket.OPEN ? 'bg-[#13c2c2]' : 'bg-rose-400'}`} />
           <span className="text-xs text-slate-500 font-medium">{ws?.readyState === WebSocket.OPEN ? '已连接' : '已断开'}</span>
        </div>
      </header>

      {/* Emotion Status Bar */}
      <AnimatePresence>
        {emotionState && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="w-full bg-white/60 backdrop-blur-sm border-b border-white/40 shadow-[0_2px_10px_rgba(0,0,0,0.02)] z-10 px-6 py-2 flex items-center justify-center gap-2 shrink-0"
          >
            <span className="text-xs text-slate-500">当前状态探测：</span>
            <span className="text-sm font-semibold text-slate-700 flex items-center gap-1">
              {emotionState.polarity === '积极' ? '☀️' : emotionState.polarity === '消极' ? '🌧️' : '☁️'}
              {emotionState.emotion_label}
            </span>
            <div className="flex items-center ml-2 bg-slate-100 rounded-full h-1.5 w-16 overflow-hidden">
              <div 
                className={`h-full rounded-full ${emotionState.polarity === '积极' ? 'bg-amber-400' : emotionState.polarity === '消极' ? 'bg-indigo-400' : 'bg-[#13c2c2]'}`}
                style={{ width: `${(emotionState.intensity / 10) * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-slate-400 ml-1">{emotionState.intensity}/10</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <main ref={mainRef} className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 z-10 scroll-smooth">
        <AnimatePresence initial={false}>
          {messages.map((msg) => {
            const isMe = myIdentity && msg.sender === myIdentity.nickname;
            const isSystem = msg.type === "system";
            const isAI = msg.sender === "AI 伴侣";
            
            if (isSystem) {
              return (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={msg.id} 
                  className="flex justify-center"
                >
                  <span className="text-xs bg-white/80 border border-slate-200 text-slate-500 px-4 py-1.5 rounded-full shadow-sm">
                    {msg.content}
                  </span>
                </motion.div>
              );
            }

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex w-full ${isMe ? "justify-end" : "justify-start"}`}
              >
                <div className={`flex max-w-[85%] sm:max-w-[70%] gap-3 ${isMe ? "flex-row-reverse" : "flex-row"}`}>
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm border border-slate-100 bg-white"
                  >
                    {isAI ? <Sparkles className="w-5 h-5 text-rose-400" /> : <User className="w-5 h-5 text-slate-400" />}
                  </div>
                  <div className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}>
                    <span className="text-xs text-slate-400 mb-1 px-1 font-medium">{isMe ? "我" : msg.sender}</span>
                    <div className={`px-5 py-3 shadow-sm border ${getBubbleStyle(!!isMe)}`}>
                      <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        <div className="h-4" />
      </main>

      {/* Input - Transparent Bottom Bar */}
      <footer className="p-4 bg-transparent z-10 shrink-0 pb-6 md:pb-8 relative">
        <div className="max-w-4xl mx-auto flex flex-col gap-3">
          <AnimatePresence>
            {emotionState && showSuggestions && emotionState.suggestions && emotionState.suggestions.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="flex flex-wrap gap-2 px-2"
              >
                {emotionState.suggestions.map((sug, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      if (ws) {
                        ws.send(sug);
                        setShowSuggestions(false);
                      }
                    }}
                    className="text-xs px-4 py-2 bg-white/80 backdrop-blur-md border border-[#13c2c2]/20 text-[#13c2c2] rounded-full shadow-sm hover:bg-[#13c2c2] hover:text-white transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    {sug}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
          <div className="flex items-center gap-3 w-full">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="轻声诉说..."
            className="flex-1 bg-white/70 backdrop-blur-md text-slate-800 placeholder:text-slate-400 rounded-full px-6 py-3.5 outline-none focus:ring-2 focus:ring-[#13c2c2]/50 focus:bg-white/95 transition-all border border-white/80 shadow-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            className="px-6 py-3.5 bg-[#13c2c2] text-white rounded-full hover:opacity-90 disabled:opacity-50 transition-all shadow-md active:scale-95 flex items-center justify-center gap-2 font-medium"
          >
            <Send className="w-5 h-5" />
            <span className="hidden sm:inline">发送</span>
          </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
