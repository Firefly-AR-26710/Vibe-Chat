from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from emotion_graph import emotion_graph
from database import get_db
import models
import jwt
import os

router = APIRouter(prefix="/api/emotion", tags=["emotion"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "vibechat_super_secret_key_change_me")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)

class EmotionRequest(BaseModel):
    text: str

class EmotionResponse(BaseModel):
    emotion_label: str
    intensity_score: int
    polarity: str
    keywords: List[str]

@router.post("/analyze", response_model=EmotionResponse)
async def analyze_emotion_api(
    request: EmotionRequest, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        # 调用基于 LangGraph 的情绪分析器
        from langchain_core.messages import HumanMessage
        state = {
            "messages": [HumanMessage(content=request.text)],
            "match_status": "queueing"
        }
        result = emotion_graph.invoke(state)
        
        emotion_label = result.get("emotion_label", "平静")
        intensity_score = result.get("intensity_score", 5)
        polarity = result.get("polarity", "中性")
        keywords = result.get("keywords", ["安静"])
        
        # 如果有用户登录，保存历史
        if credentials and credentials.credentials:
            try:
                payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    new_history = models.EmotionHistory(
                        user_id=user_id,
                        emotion_label=emotion_label,
                        intensity=intensity_score,
                        polarity=polarity
                    )
                    db.add(new_history)
                    db.commit()
            except Exception as e:
                print(f"Error saving history: {e}")
        
        return EmotionResponse(
            emotion_label=emotion_label,
            intensity_score=intensity_score,
            polarity=polarity,
            keywords=keywords
        )
    except Exception as e:
        # 当极度异常时（即使 fallback 也失败），返回安全降级数据
        print(f"API Error in emotion analysis: {e}")
        return EmotionResponse(
            emotion_label="平静",
            intensity_score=5,
            polarity="中性",
            keywords=["系统降级"]
        )
