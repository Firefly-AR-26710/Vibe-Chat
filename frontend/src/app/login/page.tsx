"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ArrowRight, UserPlus, LogIn, ArrowLeft } from "lucide-react";

export default function Login() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("请填写用户名和密码");
      return;
    }
    setLoading(true);

    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
    const host = window.location.hostname;
    try {
      const res = await fetch(`http://${host}:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "操作失败");
      }

      // Store token and user_id
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("username", data.username);
      localStorage.setItem("user_id", data.user_id);
      
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen items-center justify-center relative overflow-hidden bg-pink-50/30">
      {/* Background Dreamy Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-cyan-200/40 rounded-full blur-[100px] opacity-70" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-pink-200/50 rounded-full blur-[100px] opacity-70" />

      <button 
        onClick={() => router.push("/")} 
        className="absolute top-8 left-8 p-3 hover:bg-white/40 rounded-full transition-colors text-slate-500 backdrop-blur-sm z-20"
      >
        <ArrowLeft className="w-5 h-5" />
      </button>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="z-10 w-full max-w-md p-8 bg-white/40 backdrop-blur-xl border border-white/60 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.05)] relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-300 to-pink-300 opacity-80" />
        
        <div className="text-center mb-8 mt-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-800 mb-2">
            {isLogin ? "欢迎回来" : "遇见共鸣"}
          </h1>
          <p className="text-slate-500 text-sm">
            {isLogin ? "登录以回顾你的专属情绪轨迹" : "注册账号，让情绪的涟漪留下痕迹"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1 ml-1">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-white/60 border border-white/80 rounded-2xl px-4 py-3 text-slate-800 outline-none focus:ring-2 focus:ring-pink-300 transition-all placeholder:text-slate-400"
                placeholder="你的称呼"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1 ml-1">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/60 border border-white/80 rounded-2xl px-4 py-3 text-slate-800 outline-none focus:ring-2 focus:ring-pink-300 transition-all placeholder:text-slate-400"
                placeholder="******"
              />
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: 'auto' }} 
                exit={{ opacity: 0, height: 0 }}
                className="text-rose-500 text-sm text-center bg-rose-50/50 py-2 rounded-xl border border-rose-100"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl bg-gradient-to-r from-pink-400 to-rose-400 text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 shadow-lg shadow-pink-200"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isLogin ? <LogIn className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />)}
            {isLogin ? "登 录" : "注 册"}
          </button>
        </form>

        <div className="mt-8 text-center">
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-slate-500 hover:text-pink-500 transition-colors"
          >
            {isLogin ? "还没有账号？点击注册" : "已有账号？点击登录"} <ArrowRight className="inline w-3 h-3 ml-1" />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
