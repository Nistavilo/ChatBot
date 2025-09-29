from typing import Dict
from memory import add_to_history, get_history, clear_history
from commands import handle_command
from ollama_client import ask_ollama, OllamaError
from config import DEFAULT_MODEL

class ChatBot:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def process_input(self, user_input: str) -> Dict[str, str]:
        user_input = user_input.strip()
        if not user_input:
            return {"type": "empty", "response": "Boş giriş."}

        cmd = handle_command(user_input)
        if cmd:
            action = cmd.get("action")
            resp = cmd["response"]
            if action == "exit":
                return {"type": "exit", "response": resp}
            if action == "clear_memory":
                clear_history()
                return {"type": "command", "response": resp}
            if action == "set_model":
                new_model = (cmd.get("payload") or {}).get("model")
                if new_model:
                    self.model = new_model
                    return {"type": "command", "response": resp}
            return {"type": "command", "response": resp}

        try:
            hist = get_history()
            add_to_history("user", user_input)
            answer = ask_ollama(user_input, model=self.model, history=hist, use_history=True)
            add_to_history("assistant", answer)
            return {"type": "chat", "response": answer}
        except OllamaError as e:
            return {"type": "error", "response": f"Model hatası: {e}"}
        except Exception as e:
            return {"type": "error", "response": f"Genel hata: {e}"}