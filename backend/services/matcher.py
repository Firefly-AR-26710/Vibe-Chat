import asyncio
import json
import uuid
import time
from typing import Optional, Tuple
from redis_client import redis_pool
import redis.asyncio as redis

redis_client = redis.Redis(connection_pool=redis_pool)

POP_EXACT_UIDS_SCRIPT = """
local queue_key = KEYS[1]
local target_uids = ARGV

local items = redis.call('lrange', queue_key, 0, -1)
local item_set = {}
for i, item in ipairs(items) do
    item_set[item] = true
end

for i, uid in ipairs(target_uids) do
    if not item_set[uid] then
        return 0
    end
end

for i, uid in ipairs(target_uids) do
    redis.call('lrem', queue_key, 1, uid)
end

return 1
"""

async def enqueue_user(user_id: str, emotion_label: str, intensity: int, polarity: str, keywords: list) -> None:
    queue_key = f"queue:polarity:{polarity}"
    user_data = {
        "user_id": user_id,
        "emotion_label": emotion_label,
        "intensity": intensity,
        "polarity": polarity,
        "keywords": keywords,
        "timestamp": time.time()
    }
    # Save user data
    await redis_client.set(f"user_data:{user_id}", json.dumps(user_data), ex=3600)
    # Add to queue
    await redis_client.rpush(queue_key, user_id)

async def try_match_group(queue_key: str, required_count: int, grace_period: int = 18) -> bool:
    """Try to form a group of required_count from active users."""
    user_ids = await redis_client.lrange(queue_key, 0, -1)
    user_ids = [uid.decode("utf-8") if isinstance(uid, bytes) else uid for uid in user_ids]
    
    active_uids = []
    for uid in user_ids:
        data_str = await redis_client.get(f"user_data:{uid}")
        if data_str:
            data = json.loads(data_str)
            # Check if user is still actively waiting (hasn't timed out + grace)
            if time.time() - data.get("timestamp", 0) < grace_period:
                active_uids.append(uid)
                
    if len(active_uids) >= required_count:
        target_uids = active_uids[:required_count]
        # Atomically remove them from queue
        success = await redis_client.eval(POP_EXACT_UIDS_SCRIPT, 1, queue_key, *target_uids)
        if success == 1:
            # Create a new room for these users
            new_room_id = str(uuid.uuid4())
            for uid in target_uids:
                await redis_client.set(f"match:{uid}", new_room_id, ex=3600)
            return True
    return False

async def match_user(user_id: str, emotion_label: str, polarity: str, keywords: list, timeout: int = 15) -> Tuple[Optional[str], bool]:
    start_time = time.time()
    queue_key = f"queue:polarity:{polarity}"
    
    while time.time() - start_time < timeout:
        # Check if matched by someone else or ourselves
        room_id = await redis_client.get(f"match:{user_id}")
        if room_id:
            return room_id.decode("utf-8") if isinstance(room_id, bytes) else room_id, False
            
        # Try to match 3 people
        matched = await try_match_group(queue_key, required_count=3, grace_period=timeout + 3)
        if matched:
            room_id = await redis_client.get(f"match:{user_id}")
            if room_id:
                return room_id.decode("utf-8") if isinstance(room_id, bytes) else room_id, False
                
        await asyncio.sleep(1)
        
    # Timeout reached. Try to match 2 people.
    matched = await try_match_group(queue_key, required_count=2, grace_period=timeout + 3)
    if matched:
        room_id = await redis_client.get(f"match:{user_id}")
        if room_id:
            return room_id.decode("utf-8") if isinstance(room_id, bytes) else room_id, False

    # Check one last time if we got grabbed in the final second
    room_id = await redis_client.get(f"match:{user_id}")
    if room_id:
        return room_id.decode("utf-8") if isinstance(room_id, bytes) else room_id, False
        
    # Remove ourselves from queue to prevent being picked up later
    await redis_client.lrem(queue_key, 1, user_id)

    # Return None to indicate timeout
    return None, False
