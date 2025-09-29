from collections import deque
from typing import List, Dict, Deque
from config import MAX_HISTORY_ITEMS

class ConversationMemory:
    def __init__(self, max_items: int = MAX_HISTORY_ITEMS):
        self._history: Deque[Dict[str, str]] = deque(maxlen=max_items)

    def add(self, role: str, content: str):
        self._history.append({"role": role, "content": content})

    def get(self) -> List[Dict[str, str]]:
        return list(self._history)

    def clear(self):
        self._history.clear()

_memory = ConversationMemory()

def add_to_history(role: str, content: str):
    _memory.add(role, content)

def get_history() -> List[Dict[str, str]]:
    return _memory.get()

def clear_history():
    _memory.clear()