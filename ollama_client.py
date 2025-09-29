import os
import re
import sys
import time
import shlex
import subprocess
from typing import List, Dict, Optional, Iterable

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
FALLBACK_MODELS = [m.strip() for m in os.getenv("OLLAMA_FALLBACK_MODELS", "mistral,phi3").split(",") if m.strip()]
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")
GENERATION_PARAMS = {
    "temperature": float(os.getenv("GEN_TEMPERATURE", "0.7")),
    "top_p": float(os.getenv("GEN_TOP_P", "0.9")),
    "num_predict": int(os.getenv("GEN_NUM_PREDICT", "-1")),   
}

TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT", "180"))  
PULL_IDLE_RESET = 600  
DEBUG = os.getenv("OLLAMA_DEBUG", "1") == "1"

CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0B-\x1F\x7F]')



def dlog(*a):
    if DEBUG:
        print("[OLLAMA-DEBUG]", *a, file=sys.stderr)

def sanitize(text: str) -> str:
    return CONTROL_CHAR_PATTERN.sub('', text).strip()

def build_prompt(history: List[Dict[str, str]], user_input: str) -> str:
    """
    Basit bir sohbet formatı. Gelişmiş format için role bazlı (system/user/assistant) JSON -> string dönüşü
    veya OpenAI benzeri işaretleme yapılabilir.
    """
    lines = [f"System: {SYSTEM_PROMPT}"]
    for msg in history:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append(f"User: {user_input}")
    lines.append("Assistant:")
    return "\n".join(lines)

def model_installed(model_name: str) -> bool:
    try:
        out = subprocess.check_output(["ollama", "list"], text=True)
    except Exception as e:
        dlog("ollama list alınamadı:", e)
        return False
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    for l in lines[1:]:
        parts = l.split()
        if not parts:
            continue
        name = parts[0]  
        if name.startswith(model_name + ":") or name == model_name:
            return True
    return False

def ensure_model(model: str, pull_progress=True) -> bool:
    """
    Model yoksa indir. Varsa True döner.
    """
    if model_installed(model):
        return True
    print(f"[INFO] Model '{model}' lokalde yok. İndiriliyor...")
    cmd = ["ollama", "pull", model]
    try:
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as p:
            if p.stdout:
                for line in p.stdout:
                    if pull_progress:
                        if line.startswith("pulling "):
                            sys.stdout.write("\r" + line.strip() + " " * 10)
                            sys.stdout.flush()
                        else:
                            print(line.rstrip())
            rc = p.wait()
        print()  
        if rc != 0:
            raise RuntimeError(f"Model çekme başarısız (exit={rc})")
        print(f"[INFO] '{model}' indirildi.")
        return True
    except FileNotFoundError:
        raise RuntimeError("Ollama CLI bulunamadı (PATH kontrol et).")

def select_available_model(preferred: str, fallbacks: Iterable[str]) -> str:
    if model_installed(preferred):
        return preferred
    for fb in fallbacks:
        if fb and model_installed(fb):
            print(f"[INFO] Tercih edilen model '{preferred}' yok. Fallback ile '{fb}' kullanılacak.")
            return fb

    ensure_model(preferred)
    return preferred

def _compose_generation_hint() -> str:
    """
    CLI `ollama run model "prompt"` formatı JSON param almaz; parametreleri prompt’a gömmek bir hile.
    Bazı modeller bu ipuçlarını dikkate almayabilir. HTTP API kullanırsan gerçek paramlara geçebilirsin.
    """
    hints = []
    if GENERATION_PARAMS.get("temperature") is not None:
        hints.append(f"temperature={GENERATION_PARAMS['temperature']}")
    if GENERATION_PARAMS.get("top_p") is not None:
        hints.append(f"top_p={GENERATION_PARAMS['top_p']}")
    if GENERATION_PARAMS.get("num_predict", -1) >= 0:
        hints.append(f"max_tokens={GENERATION_PARAMS['num_predict']}")
    if not hints:
        return ""
    return f"[GENERATION_HINT: {' '.join(hints)}]\n"


class OllamaError(Exception):
    pass

def _run_cli_blocking(model: str, final_prompt: str) -> str:
    cmd = ["ollama", "run", model, final_prompt]
    dlog("Çalıştırılıyor (blocking):", shlex.join(cmd))
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        raise OllamaError(f"Inference zaman aşımı ({TIMEOUT_SECONDS}s)")
    except FileNotFoundError:
        raise OllamaError("Ollama CLI bulunamadı.")
    elapsed = time.time() - t0
    dlog(f"Return code={proc.returncode} elapsed={elapsed:.2f}s stdout_len={len(proc.stdout)} stderr_len={len(proc.stderr)}")
    if proc.returncode != 0:
        raise OllamaError(f"CLI hata kodu={proc.returncode}\nSTDERR:\n{proc.stderr}")
    if not proc.stdout.strip():
        dlog("UYARI: stdout boş.")
    return sanitize(proc.stdout)

def _run_cli_stream(model: str, final_prompt: str) -> str:

    cmd = ["ollama", "run", model, final_prompt]
    dlog("Çalıştırılıyor (stream):", shlex.join(cmd))
    start = time.time()
    output_chunks: List[str] = []
    try:
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        ) as p:
            last_activity = time.time()
            while True:
                ret = p.poll()
                line = None
                if p.stdout:
                    line = p.stdout.readline()
                if line:
                    last_activity = time.time()
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    output_chunks.append(line)
                else:
                    # Çıkış yok
                    time.sleep(0.05)
                # Timeout kontrol (sadece tamamen sessizlikte)
                if (time.time() - last_activity) > TIMEOUT_SECONDS:
                    p.kill()
                    raise OllamaError(f"Streaming sırasında {TIMEOUT_SECONDS}s aktivite yok.")
                if ret is not None:
                    # Process bitti
                    break
            stderr_full = p.stderr.read() if p.stderr else ""
            if p.returncode != 0:
                raise OllamaError(f"CLI hata kodu={p.returncode}\nSTDERR:\n{stderr_full}")
    except FileNotFoundError:
        raise OllamaError("Ollama CLI bulunamadı.")
    combined = "".join(output_chunks)
    return sanitize(combined)

def ask_ollama(
    prompt: str,
    model: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    use_history: bool = False,
    ensure: bool = True,
    stream: bool = False,
    allow_fallback: bool = True
) -> str:

    chosen = model or DEFAULT_MODEL
    if allow_fallback:
        chosen = select_available_model(chosen, FALLBACK_MODELS)
    elif ensure:
        ensure_model(chosen)

    if use_history and history:
        base_prompt = build_prompt(history, prompt)
    else:
        base_prompt = f"System: {SYSTEM_PROMPT}\nUser: {prompt}\nAssistant:"

    final_prompt = _compose_generation_hint() + base_prompt

    dlog("Final prompt (ilk 250 char):", final_prompt[:250].replace("\n", "\\n"))
    if stream:
        return _run_cli_stream(chosen, final_prompt)
    return _run_cli_blocking(chosen, final_prompt)