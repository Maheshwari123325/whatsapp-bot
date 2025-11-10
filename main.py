def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are an AI ordering assistant."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        print("🔹 Status Code:", response.status_code)
        print("🔹 Raw Response:", response.text[:800])

        if response.status_code == 401:
            return "⚠ Invalid OpenRouter API key. Please check your Render environment variable."

        result = response.json()
        choices = result.get("choices")
        if not choices:
            return f"⚠ No choices field in AI response: {result}"

        ai_reply = choices[0].get("message", {}).get("content")
        if not ai_reply:
            return f"⚠ AI returned no text. Raw: {result}"
        return ai_reply.strip()

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Connection problem with AI server."
