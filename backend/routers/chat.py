from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
import random
from services.matcher import enqueue_user, match_user, redis_client

router = APIRouter(prefix="/api/ws", tags=["websocket"])

class MatchRequest(BaseModel):
    user_id: str
    emotion_label: str
    intensity: int
    polarity: str = "中性"
    keywords: List[str] = []

ADJECTIVES = ["勇敢", "忧郁", "快乐", "神秘", "平静", "焦虑", "温柔", "暴躁", "慵懒", "热情"]
ANIMALS = ["狮子", "猫头鹰", "海豚", "狐狸", "水母", "树懒", "熊猫", "狼", "蝴蝶", "企鹅"]
COLORS = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#6366f1"]

async def generate_identity(client_id: str):
    emotion_label = ""
    try:
        user_data_str = await redis_client.get(f"user_data:{client_id}")
        if user_data_str:
            data = json.loads(user_data_str)
            emotion_label = data.get("emotion_label", "")
    except Exception:
        pass
        
    prefix = emotion_label if emotion_label else random.choice(ADJECTIVES)
    return {
        "nickname": f"{prefix}的{random.choice(ANIMALS)}",
        "color": random.choice(COLORS)
    }

class ConnectionManager:
    def __init__(self):
        # Maps room_id to list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Maps client_id to identity
        self.identities: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, room_id: str, client_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        
        if client_id not in self.identities:
            self.identities[client_id] = await generate_identity(client_id)

    def disconnect(self, websocket: WebSocket, room_id: str, client_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        # We don't delete identity immediately in case they reconnect quickly

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.post("/match")
async def request_match(request: MatchRequest):
    """
    Endpoint for frontend to request a match and wait for a room ID.
    """
    from fastapi import HTTPException
    import logging
    try:
        await enqueue_user(
            user_id=request.user_id,
            emotion_label=request.emotion_label,
            intensity=request.intensity,
            polarity=request.polarity,
            keywords=request.keywords
        )
        room_id, is_ai = await match_user(
            user_id=request.user_id,
            emotion_label=request.emotion_label,
            polarity=request.polarity,
            keywords=request.keywords
        )
        
        return {
            "room_id": room_id,
            "is_ai_companion": is_ai
        }
    except Exception as e:
        logging.error(f"Error during match: {e}")
        raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")

@router.websocket("/chat/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    await manager.connect(websocket, room_id, client_id)
    
    identity = manager.identities[client_id]
    
    is_ai_room = room_id.startswith("ai_room_")
    ai_context_str = None
    if is_ai_room:
        # Load the initial context for the AI from Redis
        ai_context_str = await redis_client.get(f"ai_context:{room_id}")
    
    join_msg = json.dumps({
        "type": "system", 
        "content": f"【{identity['nickname']}】加入了房间。", 
        "sender": "系统"
    })
    await manager.broadcast(join_msg, room_id)
    
    # Notify user of their own identity
    identity_msg = json.dumps({
        "type": "identity",
        "nickname": identity["nickname"],
        "color": identity["color"]
    })
    await websocket.send_text(identity_msg)
    
    if is_ai_room:
        intro_text = "你好，我是你的 AI 伴侣。我在这里倾听你的声音。"
        if ai_context_str:
            ai_context = json.loads(ai_context_str)
            emotion_label = ai_context.get("emotion_label", "")
            intro_text = f"你好，我是你的专属伴侣。我感觉到你现在的状态是【{emotion_label}】。想和我聊聊吗？"
            
        ai_intro = json.dumps({
            "type": "message",
            "content": intro_text,
            "sender": "AI 伴侣",
            "color": "#94a3b8" # gray color for AI
        })
        await websocket.send_text(ai_intro)

    try:
        while True:
            data = await websocket.receive_text()
            # Expecting data to be a message text
            message = json.dumps({
                "type": "message", 
                "content": data, 
                "sender": identity["nickname"],
                "color": identity["color"]
            })
            await manager.broadcast(message, room_id)
            
            # AI response trigger
            if is_ai_room:
                from llm_factory import get_llm
                from langchain_core.messages import SystemMessage, HumanMessage
                llm = get_llm()
                
                async def ai_respond():
                    try:
                        sys_prompt = "你是一个富有同理心的匿名社交伴侣。请用简短、温柔的中文（1-2句话）回应用户，给予他们情绪价值。"
                        if ai_context_str:
                            ai_context = json.loads(ai_context_str)
                            sys_prompt += f" 用户当前的情绪是：{ai_context.get('emotion_label')}（极性：{ai_context.get('polarity')}，强度：{ai_context.get('intensity')}/10）。"
                            
                        resp = await llm.ainvoke([
                            SystemMessage(content=sys_prompt),
                            HumanMessage(content=data)
                        ])
                        ai_msg = json.dumps({
                            "type": "message", 
                            "content": resp.content, 
                            "sender": "AI 伴侣",
                            "color": "#94a3b8"
                        })
                        await manager.broadcast(ai_msg, room_id)
                    except Exception as e:
                        print("AI error:", e)
                        
                asyncio.create_task(ai_respond())
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, client_id)
        leave_msg = json.dumps({
            "type": "system", 
            "content": f"【{identity['nickname']}】离开了房间。", 
            "sender": "系统"
        })
        await manager.broadcast(leave_msg, room_id)
