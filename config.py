from __future__ import annotations
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  

BASE_DIR = Path(__file__).parent

if load_dotenv:
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def _to_bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on", "evet")


def _to_int(val: str | None, default: int) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _to_float(val: str | None, default: float) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _read_file_if_exists(path_str: str | None) -> str | None:
    if not path_str:
        return None
    p = (BASE_DIR / path_str).resolve()
    if p.is_file():
        try:
            return p.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


DEFAULT_MODEL = os.getenv("CHATBOT_DEFAULT_MODEL", "llama3")
MODEL_TEMPERATURE = _to_float(os.getenv("CHATBOT_TEMPERATURE"), 0.7)
TOP_P = _to_float(os.getenv("CHATBOT_TOP_P"), 0.9)
NUM_PREDICT = _to_int(os.getenv("CHATBOT_NUM_PREDICT"), 512)
MAX_HISTORY_ITEMS = _to_int(os.getenv("CHATBOT_MAX_HISTORY"), 30)
TIMEOUT_SECONDS = _to_int(os.getenv("CHATBOT_TIMEOUT"), 120)
ENABLE_STREAM = _to_bool(os.getenv("CHATBOT_ENABLE_STREAM"), False)

_default_system_prompt = (
    "Sen yardımcı, öz ve açıklayıcı bir asistansın. Yanıtlarında Türkçe kullan."
)
_system_prompt_file_content = _read_file_if_exists(os.getenv("CHATBOT_SYSTEM_PROMPT_FILE"))
SYSTEM_PROMPT = (
    _system_prompt_file_content
    or os.getenv("CHATBOT_SYSTEM_PROMPT")
    or _default_system_prompt
)


GENERATION_PARAMS = {
    "num_predict": NUM_PREDICT,
    "top_p": TOP_P,
    "temperature": MODEL_TEMPERATURE,
}

def config_summary() -> str:
    """Debug amaçlı kısa özet."""
    return (
        "== Chatbot Config ==\n"
        f"Model: {DEFAULT_MODEL}\n"
        f"TEMPERATURE: {MODEL_TEMPERATURE}\n"
        f"TOP_P: {TOP_P}\n"
        f"NUM_PREDICT: {NUM_PREDICT}\n"
        f"MAX_HISTORY_ITEMS: {MAX_HISTORY_ITEMS}\n"
        f"TIMEOUT_SECONDS: {TIMEOUT_SECONDS}\n"
        f"ENABLE_STREAM: {ENABLE_STREAM}\n"
        f"SYSTEM_PROMPT(len): {len(SYSTEM_PROMPT)}\n"
    )