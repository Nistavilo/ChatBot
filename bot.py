from typing import Optional, Dict
from memory import add_to_history, get_history, clear_history
from commands import handle_command
from ollama_client import ask_ollama, OllamaError
from config import DEFAULT_MODEL
 
class ChatBot:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def process_input(self,user_input:str) -> Dict[str, str]:

        user_input = user_input.strip()
        if not user_input:
            return {"type": "empty", "response": "Boş mesaj gönderilemez."}
        
        cmd_result = handle_command(user_input)
        if cmd_result:
            action = cmd_result.get("action")
            response = cmd_result["response"]

            if action == "exit":
                return {"type": "exit", "response": response}
            if action == "clear_memory":
                clean_history()
                return {"type": "command", "response": response}
            
            return {"type": "command", "response": response}
        
        try:
            hist = get_history()
            add_to_history("user",user_input)
            answer = ask_ollama(user_input ,model=self.model)
            add_to_history("assistant", answer)
            return {"type": "chat", "response": answer}
        except OllamaError as e:
            return{"type": "error","response":f"Model Hatası:{e}"}
        except Exception as e:
            return{"type": "error","response":f"Bilinmeyen Hata:{e}"}