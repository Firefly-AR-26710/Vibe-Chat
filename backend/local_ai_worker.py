import os
import json
import redis
import time
from dotenv import load_dotenv

load_dotenv()

# Set to local mode when running this worker so it doesn't push to redis recursively
os.environ["USE_REMOTE_AI_WORKER"] = "false"

from langchain_core.messages import messages_from_dict, messages_to_dict
from emotion_graph import _emotion_graph

# Replace with the remote server's IP and port (Added password to pass protected mode)
REMOTE_REDIS_URL = os.getenv("REMOTE_REDIS_URL", "redis://:VibeChat2026Secure@8.159.148.30:6381/0")

print(f"Starting Local AI Worker...")
print(f"Connecting to Remote Redis: {REMOTE_REDIS_URL}")
print(f"Make sure you have your local .env configured with Gemini API keys!")

try:
    r = redis.Redis.from_url(
        REMOTE_REDIS_URL, 
        decode_responses=True, 
        health_check_interval=30,
        socket_keepalive=True
    )
    r.ping()
    print("Connected to remote Redis successfully!")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    exit(1)

print("Listening for AI tasks...")

while True:
    try:
        # Block until a task is available
        # health_check_interval and socket_keepalive prevent NAT drops
        response = r.brpop("ai_task_queue", timeout=0)
        if response:
            _, task_json = response
            task_data = json.loads(task_json)
            
            task_id = task_data.get("task_id")
            state = task_data.get("state", {})
            
            print(f"Received task: {task_id}")
            
            if "messages" in state:
                state["messages"] = messages_from_dict(state["messages"])
                
            print("Executing local LLM...")
            
            start_time = time.time()
            # Invoke the local emotion graph which uses the local Gemini API
            result = _emotion_graph.invoke(state)
            
            print(f"Execution finished in {time.time() - start_time:.2f}s")
            
            if "messages" in result:
                result["messages"] = messages_to_dict(result["messages"])
                
            # Push result back to remote Redis
            r.lpush(f"ai_result:{task_id}", json.dumps(result))
            # Set an expiry so keys don't linger if the server crashes
            r.expire(f"ai_result:{task_id}", 300)
            print(f"Result for {task_id} sent back to remote server.\n")
            
    except (redis.exceptions.TimeoutError, TimeoutError, redis.exceptions.ConnectionError):
        # Reconnect automatically on timeout/connection drops without spamming
        time.sleep(1)
    except Exception as e:
        print(f"Error processing task: {e}")
        time.sleep(2)
