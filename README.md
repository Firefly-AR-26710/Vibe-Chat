# VibeChat — AI 驱动的情绪社交

> **产品介绍（100字以内）：**
> VibeChat 是一款基于 AI 情绪分析的匿名社交应用。它能精准识别用户情绪并匹配同频陌生人。最特别之处是其“无缝 AI 兜底”机制：无人匹配时，专属 AI 伴侣会主动倾听。我们致力于打造一个治愈、零压力的心灵树洞。

VibeChat 是一款基于情绪识别的匿名社交 Web 应用。当用户输入一段文字后，系统会通过大语言模型（LLM）分析其中的情绪色彩（情绪标签、极性、强度等），并将情绪状态相近的用户自动匹配到同一段匿名对话中。如果在设定时间内未匹配到真人，系统将无缝分配一个 AI 伴侣来倾听你的声音。

## 🔗 线上演示

- **演示地址**：`[请在此处填写公网部署后的演示链接]`
- **测试说明**：本应用支持完全匿名使用，无需注册，输入想说的话即可体验核心匹配流程。*(如有特殊访问账号或白名单要求，请在此处补充说明)*

## 🌟 核心特性

- **AI 情绪雷达**：准确识别用户输入的情绪标签与极性，并将状态量化。
- **情感共鸣匹配**：基于情绪状态的动态队列匹配，连接同频的灵魂。
- **完全匿名交流**：自动生成随机昵称（如“勇敢的狮子”）和专属颜色标识，保护隐私。
- **无缝 AI 兜底**：当队列中无人时，温暖的 AI 伴侣会主动破冰并陪伴聊天。
- **现代化 UI 设计**：基于 Next.js 与 Tailwind CSS 构建，适配沉浸式黑暗模式。

---

## 🛠 技术栈

- **前端**：Next.js, React, Tailwind CSS, Framer Motion
- **后端**：FastAPI, Python 3, Uvicorn
- **AI 逻辑**：LangChain, LangGraph
- **缓存与队列**：Redis
- **实时通信**：WebSockets

---

## 🚀 快速启动

本项目支持 **Docker 一键部署** 与 **本地环境独立运行** 两种方式。

### 方式一：Docker 一键部署 (推荐)

请确保本地已安装 Docker 和 Docker Compose。

1. **配置环境变量**：参考下文的 [LLM API 配置]，在 `backend` 目录下创建并填写 `.env` 文件。
2. **启动服务**：在项目根目录（`docker-compose.yml` 所在目录）执行以下命令：
   ```bash
   docker-compose up -d --build
   ```
3. 启动完成后，即可访问：
   - 前端页面：[http://localhost:3000](http://localhost:3000)
   - 后端 API：[http://localhost:8000](http://localhost:8000)

### 方式二：本地分别运行

#### 1. 环境准备

请确保你已经安装了以下环境：
- Node.js (v18+)
- Python 3.9+
- Redis (本地运行或提供远程 URL)

### 2. LLM API 配置 (双标准适配)

本项目完全支持 **OpenAI** 和 **Anthropic** 两种标准接口。你只需在 `backend/.env` 文件中配置对应的环境变量即可自由切换。

在 `backend` 目录下创建 `.env` 文件：

**如果你使用 OpenAI 标准接口：**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
# 可选：如果你使用代理或兼容接口
# OPENAI_BASE_URL=https://api.deepseek.com/v1
```

**如果你使用 Anthropic 标准接口：**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 3. 运行后端 (FastAPI)

```bash
cd backend
# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 下使用 venv\Scripts\activate
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000
```
后端默认运行在 `http://localhost:8000`。

### 4. 运行前端 (Next.js)

```bash
cd frontend
npm install
npm run dev
```
前端默认运行在 `http://localhost:3000`。

---

## 📖 核心接口文档

- `POST /api/emotion/analyze`
  - 传入一段文本，返回分析后的 `emotion_label`, `intensity_score`, `polarity` 和 `keywords`。
- `POST /api/ws/match`
  - 基于极性和标签寻找匹配用户，若 15 秒内未找到则分配 `ai_room_xxx`。
- `WebSocket /api/ws/chat/{room_id}/{client_id}`
  - 建立双向匿名实时通信通道，支持人与人或人与 AI 对话。
