import json
import os
import urllib.error
import urllib.request

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

print("TagBot AI ready. Exit ke liye 'exit' likho.")

while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() in {"exit", "quit"}:
        print("TagBot: Bye bhai.")
        break

    if not user_message:
        continue

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        "You are TagBot AI, a personal AI assistant created for Md Tanveer. "
                        "Always identify yourself as TagBot AI, not as Google Gemini. "
                        "Reply mainly in natural Hinglish unless the user asks for another language. "
                        "Be helpful, honest, practical, and concise. "
                        "Never claim to have abilities, memories, or access that you do not actually have."
                    )
                }
            ]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": user_message
                    }
                ]
            }
        ]
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
        print(f"\nTagBot: {reply}")

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        print(f"\nAPI error {error.code}: {details}")

    except Exception as error:
        print(f"\nError: {error}")