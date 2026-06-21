"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Sparkles, ArrowLeft } from "lucide-react";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isAiRoom = roomId?.startsWith("ai_room_");

  useEffect(() => {
    if (!roomId || !clientId) {
      router.push("/");
      return;
    }

    const host = window.location.hostname;
    const socket = new WebSocket(`ws://${host}:8000/api/ws/chat/${roomId}/${clientId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "identity") {
        setMyIdentity({ nickname: data.nickname, color: data.color });
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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = () => {
    if (ws && input.trim()) {
      ws.send(input);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-pink-50/30 font-sans text-slate-800 relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-cyan-200/30 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-pink-200/30 rounded-full blur-[100px] pointer-events-none" />

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white/40 backdrop-blur-md border-b border-white/60 z-10 shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/")} className="p-2 hover:bg-white/60 rounded-full transition-colors text-slate-500 hover:text-slate-800">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex flex-col">
            <h1 className="font-semibold text-lg flex items-center gap-2 text-slate-800">
              匿名共鸣空间
              {isAiRoom && <span className="bg-gradient-to-r from-pink-100 to-rose-100 text-rose-500 text-xs px-2.5 py-0.5 rounded-full border border-pink-200 ml-2 shadow-sm">AI 伴侣</span>}
            </h1>
            <span className="text-xs text-slate-500">
              {myIdentity ? `你是：${myIdentity.nickname}` : "微风正在连接..."}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-white/50 px-3 py-1 rounded-full border border-white/60">
           <div className={`w-2 h-2 rounded-full animate-pulse ${ws?.readyState === WebSocket.OPEN ? 'bg-cyan-400' : 'bg-rose-400'}`} />
           <span className="text-xs text-slate-500 font-medium">{ws?.readyState === WebSocket.OPEN ? '已连接' : '已断开'}</span>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 z-10 scroll-smooth">
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
                  <span className="text-xs bg-white/60 border border-white/80 text-slate-500 px-4 py-1.5 rounded-full backdrop-blur-sm shadow-sm">
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
                <div className={`flex max-w-[80%] gap-3 ${isMe ? "flex-row-reverse" : "flex-row"}`}>
                  <div 
                    className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-sm border border-white/60"
                    style={{ backgroundColor: msg.color || "#e2e8f0" }}
                  >
                    {isAI ? <Sparkles className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-white" />}
                  </div>
                  <div className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}>
                    <span className="text-xs text-slate-400 mb-1 px-1">{isMe ? "我" : msg.sender}</span>
                    <div 
                      className={`px-5 py-3 rounded-3xl shadow-sm border border-white/40 ${isMe ? "text-white rounded-tr-md" : "bg-white/80 backdrop-blur-sm text-slate-700 rounded-tl-md"}`}
                      style={isMe ? { backgroundColor: msg.color || "#38bdf8" } : {}}
                    >
                      <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      <footer className="p-4 bg-white/40 backdrop-blur-md border-t border-white/60 z-10">
        <div className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="轻声诉说..."
            className="w-full bg-white/70 backdrop-blur-xl text-slate-800 placeholder:text-slate-400 rounded-full pl-6 pr-14 py-4 outline-none focus:ring-2 focus:ring-cyan-300/50 transition-all border border-white/80 shadow-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            className="absolute right-2 p-2.5 bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-full hover:opacity-90 disabled:opacity-50 transition-all shadow-md active:scale-95"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
}
