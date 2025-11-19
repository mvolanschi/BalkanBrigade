import json
from pathlib import Path
from typing import Optional

PROMPTS_PATH = Path(__file__).with_name("system_prompts.json")

try:
    _PROMPTS = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
except Exception:
    _PROMPTS = {}


def get_prompt(technicality: int, politeness: int, difficulty: int) -> Optional[str]:
    key = f"{technicality}_{politeness}_{difficulty}"
    return _PROMPTS.get(key) or _PROMPTS.get("default")
    