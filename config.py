"""
config.py
Genel yapılandırma ve sabitler.
İleride .env veya YAML tabanlı konfigürasyona evrilebilir.
"""

DEFAULT_MODEL = "llama3"
MODEL_TEMPERATURE = 0.7
MAX_HISTORY_ITEMS = 30          # Hafızada tutulacak max mesaj çifti
TIMEOUT_SECONDS = 120           # Ollama isteği zaman aşımı
ENABLE_STREAM = False           # Streaming desteklenecekse True yapılabilir (CLI parametreleri ile)
SYSTEM_PROMPT = (
    "Sen yardımcı, öz ve açıklayıcı bir asistansın. "
    "Yanıtlarında Türkçe kullan ve gerektiğinde kısa örnekler ver."
)

# Geliştirilebilir parametre havuzu
GENERATION_PARAMS = {
    "num_predict": 512,
    "top_p": 0.9,
    "temperature": MODEL_TEMPERATURE,
}