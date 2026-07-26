import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


# Project folder ka exact path
BASE_DIR = Path(__file__).resolve().parent.parent

# Project ki .env file load karo
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY .env file me nahi mili.")

MODEL_NAME = "gemini-3.6-flash"

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL_NAME}:generateContent"
)

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key,
}

memory_path = BASE_DIR / "data" / "memory.json"


def load_memory():
    """Laptop par saved permanent memories load karta hai."""
    try:
        with memory_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}


def save_memory(memory):
    """Permanent memories ko local JSON file me save karta hai."""
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    with memory_path.open("w", encoding="utf-8") as file:
        json.dump(
            memory,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_next_memory_key(memory):
    """Nayi memory ke liye safe unique key banata hai."""
    numbers = []

    for key in memory:
        if key.startswith("fact_"):
            try:
                numbers.append(int(key.split("_", 1)[1]))
            except ValueError:
                continue

    next_number = max(numbers, default=0) + 1
    return f"fact_{next_number}"


def extract_reply(result):
    """Gemini API response se text safely nikalta hai."""
    candidates = result.get("candidates", [])

    if not candidates:
        return "Mujhe is request ka response generate nahi mila."

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])

    text_parts = [
        part.get("text", "")
        for part in parts
        if part.get("text")
    ]

    if not text_parts:
        return "Response mila, lekin usme text available nahi tha."

    return "\n".join(text_parts)


permanent_memory = load_memory()
conversation_history = []

print("TagBot AI ready.")
print("Band karne ke liye: exit")
print("Memory save karne ke liye: remember: <baat>")
print("Saved memories dekhne ke liye: memories")
print("Saari memories delete karne ke liye: forget all")

while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() in {"exit", "quit"}:
        print("TagBot: Bye bhai.")
        break

    if not user_message:
        continue

    if user_message.lower() == "memories":
        if not permanent_memory:
            print("TagBot: Abhi koi permanent memory saved nahi hai.")
        else:
            print("TagBot: Saved permanent memories:")

            for number, fact in enumerate(
                permanent_memory.values(),
                start=1,
            ):
                print(f"{number}. {fact}")

        continue

    if user_message.lower() == "forget all":
        confirmation = input(
            "Saari memories delete karne ke liye DELETE likho: "
        ).strip()

        if confirmation == "DELETE":
            permanent_memory.clear()
            save_memory(permanent_memory)
            print("TagBot: Saari permanent memories delete kar di gayi hain.")
        else:
            print("TagBot: Memory deletion cancel kar di gayi.")

        continue

    if user_message.lower().startswith("remember:"):
        fact = user_message.split(":", 1)[1].strip()

        if not fact:
            print("TagBot: Yaad rakhne ke liye koi baat likho.")
            continue

        key = get_next_memory_key(permanent_memory)
        permanent_memory[key] = fact
        save_memory(permanent_memory)

        print(f"TagBot: Theek hai bhai, maine yaad rakh liya: {fact}")
        continue

    memory_text = "\n".join(
        f"- {value}"
        for value in permanent_memory.values()
    )

    system_prompt = (
        "You are TagBot AI, a personal AI assistant created for Md Tanveer. "
        "Always identify yourself as TagBot AI, not as Google Gemini. "
        "Reply mainly in natural Hinglish unless the user asks for another language. "
        "Be helpful, honest, practical, and concise. "
        "Use earlier messages from the current conversation when relevant. "
        "Use saved permanent memories only when relevant. "
        "Never invent memories, abilities, or access that you do not have.\n\n"
        f"Saved permanent memories:\n"
        f"{memory_text or '- No permanent memories saved yet.'}"
    )

    conversation_history.append(
        {
            "role": "user",
            "parts": [
                {
                    "text": user_message,
                }
            ],
        }
    )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": system_prompt,
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
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        reply = extract_reply(result)

        conversation_history.append(
            {
                "role": "model",
                "parts": [
                    {
                        "text": reply,
                    }
                ],
            }
        )

        print(f"\nTagBot: {reply}")

    except urllib.error.HTTPError as error:
        conversation_history.pop()

        details = error.read().decode(
            "utf-8",
            errors="replace",
        )

        print(f"\nAPI error {error.code}: {details}")

    except Exception as error:
        conversation_history.pop()
        print(f"\nError: {error}")