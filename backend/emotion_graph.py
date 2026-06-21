from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from llm_factory import get_llm

class EmotionState(TypedDict):
    text: str
    emotion_label: Optional[str]
    intensity_score: Optional[int]
    polarity: Optional[str]
    keywords: Optional[List[str]]

class EmotionOutput(BaseModel):
    emotion_label: str = Field(description="核心情绪标签（例如：快乐, 悲伤, 愤怒, 焦虑, 平静, 孤独, 期待）")
    intensity_score: int = Field(description="情绪强度得分，范围从 1 到 10")
    polarity: str = Field(description="情绪极性，必须是以下之一：'积极' (positive), '消极' (negative), '中性' (neutral)")
    keywords: List[str] = Field(description="从文本中提取的3-5个最能代表情绪或状态的关键词")

llm = get_llm()
# Use structured output for reliable JSON parsing
structured_llm = llm.with_structured_output(EmotionOutput)

def analyze_emotion(state: EmotionState) -> dict:
    text = state["text"]
    prompt = f"""
    请作为一名专业的情绪分析师，仔细阅读以下用户的输入。
    分析其中蕴含的情感色彩，并提取：
    1. 核心情绪标签
    2. 情绪强度（1-10）
    3. 情绪极性（积极、消极、中性）
    4. 代表性关键词
    
    用户输入：
    {text}
    """
    
    try:
        result = structured_llm.invoke(prompt)
        return {
            "emotion_label": result.emotion_label,
            "intensity_score": result.intensity_score,
            "polarity": result.polarity,
            "keywords": result.keywords
        }
    except Exception as e:
        # Fallback if structure parsing fails or LLM errors out (Graceful Degradation)
        print(f"LLM Emotion Analysis Error: {e}")
        return {
            "emotion_label": "平静",
            "intensity_score": 5,
            "polarity": "中性",
            "keywords": ["安静", "平淡"]
        }

graph_builder = StateGraph(EmotionState)
graph_builder.add_node("analyze_emotion", analyze_emotion)
graph_builder.add_edge(START, "analyze_emotion")
graph_builder.add_edge("analyze_emotion", END)

emotion_graph = graph_builder.compile()
