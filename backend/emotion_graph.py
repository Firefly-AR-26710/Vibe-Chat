from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from llm_factory import get_llm

class EmotionState(TypedDict):
    text: str
    emotion_label: Optional[str]
    intensity_score: Optional[int]

class EmotionOutput(BaseModel):
    emotion_label: str = Field(description="The primary emotion label (e.g., 快乐, 悲伤, 愤怒, 焦虑, 平静, 孤独, 期待)")
    intensity_score: int = Field(description="The intensity of the emotion from 1 to 10")

llm = get_llm()
# Use structured output for reliable JSON parsing
structured_llm = llm.with_structured_output(EmotionOutput)

def analyze_emotion(state: EmotionState) -> dict:
    text = state["text"]
    prompt = f"请分析以下文本所表达的情绪，并提取核心情绪标签和强度（1-10）：\n\n{text}"
    
    try:
        result = structured_llm.invoke(prompt)
        return {
            "emotion_label": result.emotion_label,
            "intensity_score": result.intensity_score
        }
    except Exception as e:
        # Fallback if structure parsing fails or LLM errors out
        return {
            "emotion_label": "平静",
            "intensity_score": 5
        }

graph_builder = StateGraph(EmotionState)
graph_builder.add_node("analyze_emotion", analyze_emotion)
graph_builder.add_edge(START, "analyze_emotion")
graph_builder.add_edge("analyze_emotion", END)

emotion_graph = graph_builder.compile()
