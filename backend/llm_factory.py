import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "anthropic":
        return ChatAnthropic(
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=0.7,
        )
    else:
        # Default to OpenAI standard interface
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            temperature=0.7,
        )
