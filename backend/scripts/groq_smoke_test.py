import os
import httpx
import asyncio

async def test_groq():
    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        print("ERROR: AI_API_KEY not set in environment.")
        return

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    tools = [{
        "type": "function",
        "function": {
            "name": "get_headcount",
            "description": "Get total active headcount",
            "parameters": {"type": "object", "properties": {}}
        }
    }]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "How many employees do we have?"}],
        "tools": tools,
        "tool_choice": "auto"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print("Response:", data)
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls")
            if tool_calls:
                print("SUCCESS: Model returned tool call:", tool_calls[0]["function"]["name"])
            else:
                print("NOTE: Model answered directly without tool call:", message.get("content"))
        except Exception as e:
            print(f"ERROR calling Groq: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())
