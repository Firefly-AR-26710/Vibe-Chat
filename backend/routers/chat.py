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
        # Clear previous match to allow fresh 15s wait
        await redis_client.delete(f"match:{request.user_id}")
        
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
        
        if room_id is None:
            return {"status": "timeout"}
            
        return {
            "status": "success",
            "room_id": room_id,
            "is_ai_companion": is_ai
        }
    except Exception as e:
        logging.error(f"Error during match: {e}")
        raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")

class FallbackRequest(BaseModel):
    user_id: str
    emotion_label: str
    intensity: int
    polarity: str
    keywords: List[str]
    fallback_type: str # "ai" or "mock_user"

@router.post("/match/fallback")
async def create_fallback_room(request: FallbackRequest):
    import uuid
    from fastapi import HTTPException
    try:
        prefix = "mock_room_" if request.fallback_type == "mock_user" else "ai_room_"
        room_id = f"{prefix}{uuid.uuid4()}"
        
        # Save context
        ai_context = {
            "emotion_label": request.emotion_label,
            "polarity": request.polarity,
            "keywords": request.keywords,
            "intensity": request.intensity,
            "mock_nickname": f"{random.choice(ADJECTIVES)}的{random.choice(ANIMALS)}",
            "mock_color": random.choice(COLORS)
        }
        await redis_client.set(f"ai_context:{room_id}", json.dumps(ai_context), ex=3600)
        
        return {
            "status": "success",
            "room_id": room_id,
            "is_ai_companion": True
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Fallback failed: {str(e)}")

@router.websocket("/chat/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    await manager.connect(websocket, room_id, client_id)
    
    identity = manager.identities[client_id]
    
    is_ai_room = room_id.startswith("ai_room_")
    is_mock_room = room_id.startswith("mock_room_")
    
    ai_context_str = None
    if is_ai_room or is_mock_room:
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
    elif is_mock_room:
        mock_nickname = "匿名网友"
        if ai_context_str:
            mock_nickname = json.loads(ai_context_str).get("mock_nickname", "匿名网友")
        mock_intro = json.dumps({
            "type": "system",
            "content": f"【{mock_nickname}】加入了房间。",
            "sender": "系统"
        })
        await websocket.send_text(mock_intro)

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
            if is_ai_room or is_mock_room:
                from emotion_graph import emotion_graph
                from langchain_core.messages import HumanMessage
                
                async def ai_respond():
                    try:
                        ai_context = json.loads(ai_context_str) if ai_context_str else {}
                        match_status = "mock_user" if is_mock_room else "ai"
                        
                        state = {
                            "messages": [HumanMessage(content=data)],
                            "match_status": match_status,
                            "emotion_label": ai_context.get("emotion_label", ""),
                            "intensity_score": ai_context.get("intensity", 5),
                            "polarity": ai_context.get("polarity", "中性"),
                        }
                        
                        # Use asyncio.to_thread to run sync graph invocation in background
                        result = await asyncio.to_thread(emotion_graph.invoke, state)
                        ai_reply = result.get("current_response", "……")
                        
                        sender_name = "AI 伴侣" if is_ai_room else ai_context.get("mock_nickname", "匿名网友")
                        sender_color = "#94a3b8" if is_ai_room else ai_context.get("mock_color", "#f59e0b")
                        
                        ai_msg = json.dumps({
                            "type": "message", 
                            "content": ai_reply, 
                            "sender": sender_name,
                            "color": sender_color
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
