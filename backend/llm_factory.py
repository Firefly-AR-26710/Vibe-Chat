import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()

def get_db_settings():
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        settings_records = db.query(models.SystemSettings).all()
        return {record.key: record.value for record in settings_records}
    except Exception:
        return {}
    finally:
        db.close()

def get_llm():
    db_settings = get_db_settings()
    
    def get_setting(key, default=""):
        return db_settings.get(key) or os.getenv(key, default)

    provider = get_setting("LLM_PROVIDER", "openai").lower()
    
    if provider == "anthropic":
        return ChatAnthropic(
            model_name=get_setting("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=get_setting("ANTHROPIC_API_KEY", ""),
            anthropic_api_url=get_setting("ANTHROPIC_BASE_URL") or None,
            temperature=0.7,
        )
    else:
        # Default to OpenAI standard interface
        return ChatOpenAI(
            model=get_setting("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=get_setting("OPENAI_API_KEY", ""),
            base_url=get_setting("OPENAI_BASE_URL") or None,
            temperature=0.7,
        )
