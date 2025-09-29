import json
from pathlib import Path

RESPONSES_PATH = Path(__file__).parent / "data" / "responses.json"

# Hazır cevapları önbelleğe al
try:
    with open(RESPONSES_PATH, "r", encoding="utf-8") as f:
        PREDEFINED = json.load(f)
except FileNotFoundError:
    PREDEFINED = {
        "selam": "Merhaba! (responses.json bulunamadı, varsayılan cevap)"
    }

def handle_command(raw_input: str):

    if not raw_input.startswith("/"):
        return None

    cmd = raw_input.strip().lstrip("/").lower()

    if cmd in ("yardım", "help"):
        return {
            "type": "command",
            "name": "yardım",
            "response": (
                "Kullanılabilir komutlar:\n"
                "/yardım  - Bu mesajı gösterir\n"
                "/selam   - Selamlama mesajı\n"
                "/çık     - Programı sonlandırır\n"
                "/temizle - Hafızayı sıfırlar\n"
            ),
            "action": None
        }

    if cmd in ("selam", "hi", "hello"):
        return {
            "type": "command",
            "name": "selam",
            "response": PREDEFINED.get("greeting", "Selam!"),
            "action": None
        }

    if cmd in ("çık", "cik", "exit", "quit"):
        return {
            "type": "command",
            "name": "çık",
            "response": PREDEFINED.get("goodbye", "Görüşmek üzere!"),
            "action": "exit"
        }

    if cmd in ("temizle", "clear"):
        return {
            "type": "command",
            "name": "temizle",
            "response": "Konuşma geçmişi sıfırlandı.",
            "action": "clear_memory"
        }

    return {
        "type": "unknown",
        "name": cmd,
        "response": f"Bilinmeyen komut: /{cmd} ( /yardım yazabilirsiniz )",
        "action": None
    }