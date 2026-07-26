import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
MEMORY_PATH = BASE_DIR / "data" / "memory.json"

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY .env file me nahi mili.")

MODEL_NAME = "gemini-3.6-flash"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL_NAME}:generateContent"
)

conversation_history = []


def load_memory():
    try:
        with MEMORY_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}


def save_memory(memory):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    with MEMORY_PATH.open("w", encoding="utf-8") as file:
        json.dump(memory, file, ensure_ascii=False, indent=2)


def get_next_memory_key(memory):
    numbers = []

    for key in memory:
        if key.startswith("fact_"):
            try:
                numbers.append(int(key.split("_", 1)[1]))
            except ValueError:
                continue

    return f"fact_{max(numbers, default=0) + 1}"


def process_local_command(message):
    permanent_memory = load_memory()
    lower_message = message.lower()

    if lower_message == "help":
        return (
            "Available commands:\n"
            "remember: <baat> — permanent memory save karo\n"
            "memories — saved memories dekho\n"
            "forget <number> — specific memory delete karo\n"
            "forget all — saari memories delete karo"
        )

    if lower_message == "memories":
        if not permanent_memory:
            return "Abhi koi permanent memory saved nahi hai."

        lines = [
            f"{number}. {fact}"
            for number, fact in enumerate(
                permanent_memory.values(),
                start=1,
            )
        ]

        return "Saved permanent memories:\n" + "\n".join(lines)

    if lower_message.startswith("remember:"):
        fact = message.split(":", 1)[1].strip()

        if not fact:
            return "Yaad rakhne ke liye koi baat likho."

        key = get_next_memory_key(permanent_memory)
        permanent_memory[key] = fact
        save_memory(permanent_memory)

        return f"Theek hai bhai, maine yaad rakh liya: {fact}"

    if lower_message.startswith("forget "):
        number_text = message.split(" ", 1)[1].strip()

        if not number_text.isdigit():
            return "Example use karo: forget 1"

        memory_items = list(permanent_memory.items())
        memory_number = int(number_text)

        if memory_number < 1 or memory_number > len(memory_items):
            return "Is number ki koi saved memory nahi hai."

        memory_key, memory_fact = memory_items[memory_number - 1]
        del permanent_memory[memory_key]
        save_memory(permanent_memory)

        return f"Memory delete kar di: {memory_fact}"

    if lower_message == "forget all":
        permanent_memory.clear()
        save_memory(permanent_memory)
        return "Saari permanent memories delete kar di gayi hain."

    return None


def ask_gemini(message):
    local_reply = process_local_command(message)

    if local_reply is not None:
        return local_reply

    permanent_memory = load_memory()

    memory_text = "\n".join(
        f"- {fact}"
        for fact in permanent_memory.values()
    )

    system_prompt = (
        "You are TagBot AI, a personal AI assistant created for Md Tanveer. "
        "Always identify yourself as TagBot AI, not as Google Gemini. "
        "Reply mainly in natural Hinglish unless another language is requested. "
        "Be honest, practical, helpful, and concise. "
        "Use earlier conversation messages and saved memories when relevant. "
        "Never invent memories, abilities, or access.\n\n"
        f"Saved permanent memories:\n"
        f"{memory_text or '- No permanent memories saved yet.'}"
    )

    conversation_history.append(
        {
            "role": "user",
            "parts": [{"text": message}],
        }
    )

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": conversation_history,
    }

    request = urllib.request.Request(
        GEMINI_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        reply = (
            result["candidates"][0]["content"]["parts"][0]["text"]
        )

        conversation_history.append(
            {
                "role": "model",
                "parts": [{"text": reply}],
            }
        )

        return reply

    except urllib.error.HTTPError as error:
        conversation_history.pop()

        details = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"API error {error.code}: {details}"
        ) from error

    except Exception:
        conversation_history.pop()
        raise


class TagBotHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in {"/", "/index.html"}:
            file_path = FRONTEND_DIR / "index.html"

            try:
                content = file_path.read_bytes()
            except FileNotFoundError:
                self.send_error(404, "frontend/index.html nahi mili.")
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404, "Not found")
            return
    def do_POST(self):
        if self.path == "/api/reset":
            conversation_history.clear()
            self.send_json({"message": "Conversation reset ho gayi."})
            return

        if self.path != "/api/chat":
            self.send_error(404, "Not found")
            return
        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            request_body = self.rfile.read(content_length)
            data = json.loads(request_body.decode("utf-8"))

            message = str(data.get("message", "")).strip()

            if not message:
                self.send_json(
                    {"error": "Message khaali nahi ho sakta."},
                    status=400,
                )
                return

            reply = ask_gemini(message)
            self.send_json({"reply": reply})

        except Exception as error:
            self.send_json(
                {"error": str(error)},
                status=500,
            )

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("127.0.0.1", 5500),
        TagBotHandler,
    )

    print("TagBot browser server ready:")
    print("http://localhost:5500")
    print("Band karne ke liye Ctrl + C dabao.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTagBot server band ho gaya.")
    finally:
        server.server_close()