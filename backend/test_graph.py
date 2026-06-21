import sys
from pprint import pprint
from langchain_core.messages import HumanMessage
from emotion_graph import emotion_graph

def run_tests():
    print("--- Test 1: Queueing Match Status ---")
    state1 = {
        "messages": [HumanMessage(content="今天工作好累，一直加班到现在，真的感觉快撑不住了。")],
        "match_status": "queueing"
    }
    result1 = emotion_graph.invoke(state1)
    print("State keys:")
    pprint(list(result1.keys()))
    print("Emotion Label:", result1.get("emotion_label"))
    print("Intensity:", result1.get("intensity_score"))
    print("Current Response:", result1.get("current_response", "None (as expected)"))
    print("\n")

    print("--- Test 2: AI Match Status ---")
    state2 = {
        "messages": [HumanMessage(content="没匹配到人，有点失落，感觉连倾诉的地方都没有了。")],
        "match_status": "ai"
    }
    result2 = emotion_graph.invoke(state2)
    print("Emotion Label:", result2.get("emotion_label"))
    print("Intensity:", result2.get("intensity_score"))
    print("Current Response:", result2.get("current_response"))
    print("\n")

    print("--- Test 3: Mock User Match Status ---")
    state3 = {
        "messages": [HumanMessage(content="哎，今天真的倒霉透了，什么事都不顺，好想找个人骂一顿。")],
        "match_status": "mock_user"
    }
    result3 = emotion_graph.invoke(state3)
    print("Emotion Label:", result3.get("emotion_label"))
    print("Intensity:", result3.get("intensity_score"))
    print("Current Response:", result3.get("current_response"))

if __name__ == "__main__":
    run_tests()
