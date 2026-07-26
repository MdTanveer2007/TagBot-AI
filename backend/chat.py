import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY .env file me nahi mili.")

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.6-flash:generateContent"
)

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key,
}

memory_path = Path("data/memory.json")


def load_memory():
    try:
        with memory_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}


def save_memory(memory):
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    with memory_path.open("w", encoding="utf-8") as file:
        json.dump(memory, file, ensure_ascii=False, indent=2)


permanent_memory = load_memory()
conversation_history = []

print("TagBot AI ready. Exit ke liye 'exit' likho.")
print("Permanent memory save karne ke liye: remember: <baat>")

while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() in {"exit", "quit"}:
        print("TagBot: Bye bhai.")
        break

    if not user_message:
        continue

    if user_message.lower().startswith("remember:"):
        fact = user_message.split(":", 1)[1].strip()

        if not fact:
            print("TagBot: Yaad rakhne ke liye koi baat likho.")
            continue

        key = f"fact_{len(permanent_memory) + 1}"
        permanent_memory[key] = fact
        save_memory(permanent_memory)

        print(f"TagBot: Theek hai bhai, maine yaad rakh liya: {fact}")
        continue

    memory_text = "\n".join(
        f"- {value}" for value in permanent_memory.values()
    )

    system_prompt = (
        "You are TagBot AI, a personal AI assistant created for Md Tanveer. "
        "Always identify yourself as TagBot AI, not as Google Gemini. "
        "Reply mainly in natural Hinglish unless the user asks for another language. "
        "Be helpful, honest, practical, and concise. "
        "Use earlier messages from the current conversation when relevant. "
        "Use the saved permanent memory below when relevant. "
        "Never invent memories or access you do not have.\n\n"
        f"Saved permanent memory:\n{memory_text or '- No saved memory yet.'}"
    )

    conversation_history.append(
        {
            "role": "user",
            "parts": [
                {
                    "text": user_message
                }
            ]
        }
    )

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": system_prompt
                }
            ]
        },
        "contents": conversation_history,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        reply = result["candidates"][0]["content"]["parts"][0]["text"]

        conversation_history.append(
            {
                "role": "model",
                "parts": [
                    {
                        "text": reply
                    }
                ]
            }
        )

        print(f"\nTagBot: {reply}")

    except urllib.error.HTTPError as error:
        conversation_history.pop()
        details = error.read().decode("utf-8", errors="replace")
        print(f"\nAPI error {error.code}: {details}")

    except Exception as error:
        conversation_history.pop()
        print(f"\nError: {error}")