from typing import TypedDict, Optional, List, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from llm_factory import get_llm
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

class EmotionState(TypedDict):
    messages: List[BaseMessage]
    match_status: str # "queueing", "user", "ai", "mock_user"
    emotion_label: Optional[str]
    intensity_score: Optional[int]
    polarity: Optional[str]
    keywords: Optional[List[str]]
    current_response: Optional[str]

class EmotionOutput(BaseModel):
    emotion_label: str = Field(description="核心情绪标签（例如：快乐, 悲伤, 愤怒, 焦虑, 平静, 孤独, 期待）")
    intensity_score: int = Field(description="情绪强度得分，范围从 1 到 10")
    polarity: str = Field(description="情绪极性，必须是以下之一：'积极' (positive), '消极' (negative), '中性' (neutral)")
    keywords: List[str] = Field(description="从文本中提取的3-5个最能代表情绪或状态的关键词")

llm = get_llm()
# Use structured output for reliable JSON parsing
structured_llm = llm.with_structured_output(EmotionOutput)

def analyze_emotion(state: EmotionState) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {}
    
    # Get the latest user message
    last_message = messages[-1].content if isinstance(messages[-1], BaseMessage) else str(messages[-1])
    
    prompt = f"""
    请作为一名专业的情绪分析师，仔细阅读以下用户的输入。
    分析其中蕴含的情感色彩，并提取：
    1. 核心情绪标签
    2. 情绪强度（1-10）
    3. 情绪极性（积极、消极、中性）
    4. 代表性关键词
    
    用户输入：
    {last_message}
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
        print(f"LLM Emotion Analysis Error: {e}")
        return {
            "emotion_label": "平静",
            "intensity_score": 5,
            "polarity": "中性",
            "keywords": ["安静", "平淡"]
        }

@tool
def get_comforting_quote(emotion_label: str) -> str:
    """获取针对特定情绪的安慰名言或建议，在需要时为用户提供心理支持。"""
    quotes = {
        "焦虑": "『与其担忧未来，不如专注于眼前的一小步。』",
        "悲伤": "『悲伤是爱曾存在过的证明。』",
        "孤独": "『世界很大，总有和你相似的灵魂在某个角落。』",
        "愤怒": "『愤怒是内心的护卫，但不要让它烧伤自己。』",
        "疲惫": "『停下来休息一下吧，你已经做得很好了。』",
        "快乐": "『把这份快乐珍藏，它会是未来日子里的光。』",
    }
    return quotes.get(emotion_label, "『一切都会过去，保持内心的平静。』")

def generate_ai_response(state: EmotionState) -> dict:
    messages = state.get("messages", [])
    emotion_label = state.get("emotion_label", "未知")
    intensity = state.get("intensity_score", 5)
    
    # Emotion-Aware Persona Prompt
    system_prompt = f"""
你现在是 VibeChat 的匿名 AI 伴侣。用户目前正处于【{emotion_label}】的情绪中（情绪强度：{intensity}/10）。
你的任务是：
1. 深入共情用户的感受，用自然、温暖、像真人朋友一样的口吻回复。
2. 避免说教或机械式的安慰。如果情绪强度很高（>7），请给予更多包容和理解。
3. 保持匿名感，不要自称是AI，用第一人称"我"与用户交流。
4. 语言简短自然，像真实的聊天消息一样。
5. 你可以使用 `get_comforting_quote` 工具来获取名言，并在聊天中自然地引用它来安慰用户（如果合适的话）。
"""
    
    try:
        # Create a ReAct agent equipped with the tool
        agent = create_react_agent(llm, tools=[get_comforting_quote], state_modifier=system_prompt)
        # The agent will autonomous run the thought-action-observation loop
        response = agent.invoke({"messages": messages})
        return {"current_response": response["messages"][-1].content}
    except Exception as e:
        print(f"LLM Response Generation Error: {e}")
        return {"current_response": "抱歉，我现在有点走神了，你能再说一遍吗？"}

def generate_mock_user_response(state: EmotionState) -> dict:
    messages = state.get("messages", [])
    emotion_label = state.get("emotion_label", "未知")
    intensity = state.get("intensity_score", 5)
    
    # Mock User Persona Prompt
    system_prompt = f"""
你现在的身份是一个真实的互联网普通用户，在 VibeChat 匿名社交平台上与对方随机匹配到了。
系统检测到对方目前处于【{emotion_label}】的情绪中（情绪强度：{intensity}/10）。
你的任务是：
1. 扮演一个有血有肉、有自己生活和烦恼的普通人，**绝对不能**暴露自己是 AI。
2. 像真人一样聊天，可以分享一点自己编造的日常小事来拉近距离，用词口语化、接地气。
3. 展现对对方情绪的理解，但方式要像普通网友，比如“哎，我懂，我前几天也这样…”
4. 回复要简短，不要像客服或心理医生那样长篇大论。可以适当带一点错别字或语气词（如：啊、哈、呢、卧槽等）。
"""
    
    prompt_messages = [SystemMessage(content=system_prompt)] + messages
    
    try:
        response = llm.invoke(prompt_messages)
        return {"current_response": response.content}
    except Exception as e:
        print(f"LLM Mock User Generation Error: {e}")
        return {"current_response": "哎，网太卡了，刚才你说啥？"}

def route_after_analysis(state: EmotionState) -> Literal["generate_ai_response", "generate_mock_user_response", "__end__"]:
    # If match status is "ai", we need to generate an AI response
    if state.get("match_status") == "ai":
        return "generate_ai_response"
    elif state.get("match_status") == "mock_user":
        return "generate_mock_user_response"
    # Otherwise, finish the graph and let backend handle matching
    return END

graph_builder = StateGraph(EmotionState)
graph_builder.add_node("analyze_emotion", analyze_emotion)
graph_builder.add_node("generate_ai_response", generate_ai_response)
graph_builder.add_node("generate_mock_user_response", generate_mock_user_response)

graph_builder.add_edge(START, "analyze_emotion")
graph_builder.add_conditional_edges(
    "analyze_emotion",
    route_after_analysis
)
graph_builder.add_edge("generate_ai_response", END)
graph_builder.add_edge("generate_mock_user_response", END)

# Compiled as a stateless graph without checkpointer
_emotion_graph = graph_builder.compile()

import os
import json
import uuid
import redis
from langchain_core.messages import messages_to_dict, messages_from_dict

class RemoteEmotionGraph:
    def __init__(self):
        self.redis_client = None

    def invoke(self, state: dict) -> dict:
        use_remote = os.getenv("USE_REMOTE_AI_WORKER", "false").lower() == "true"
        if not use_remote:
            return _emotion_graph.invoke(state)
        
        if not self.redis_client:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        
        serialized_state = dict(state)
        if "messages" in serialized_state:
            serialized_state["messages"] = messages_to_dict(serialized_state["messages"])
        
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "state": serialized_state
        }
        
        try:
            self.redis_client.lpush("ai_task_queue", json.dumps(task_data))
            response = self.redis_client.brpop(f"ai_result:{task_id}", timeout=45)
            
            if response:
                _, result_json = response
                result_data = json.loads(result_json)
                if "messages" in result_data:
                    result_data["messages"] = messages_from_dict(result_data["messages"])
                return result_data
            else:
                print("Remote AI Worker timeout!")
                return {}
        except Exception as e:
            print(f"Redis remote worker error: {e}")
            return {}

emotion_graph = RemoteEmotionGraph()
