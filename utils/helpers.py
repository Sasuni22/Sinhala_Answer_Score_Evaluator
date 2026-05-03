"""
Utility functions for SinhalaScore AI
"""


def get_score_grade(score: int) -> tuple[str, str]:
    if score >= 18:
        return "OUTSTANDING", "#c9a96e"
    elif score >= 16:
        return "EXCELLENT", "#81c784"
    elif score >= 14:
        return "VERY GOOD", "#4fc3f7"
    elif score >= 12:
        return "GOOD", "#aed581"
    elif score >= 10:
        return "SATISFACTORY", "#fff176"
    elif score >= 8:
        return "NEEDS IMPROVEMENT", "#ffb74d"
    else:
        return "INSUFFICIENT", "#e57373"


def get_criteria_color(awarded: int, max_marks: int) -> str:
    ratio = awarded / max_marks if max_marks > 0 else 0
    if ratio >= 0.85:
        return "#81c784"
    elif ratio >= 0.65:
        return "#4fc3f7"
    elif ratio >= 0.45:
        return "#fff176"
    else:
        return "#e57373"


def format_score_percentage(score: int, max_score: int = 20) -> float:
    return round((score / max_score) * 100, 1)


def check_ollama_available(model: str = "gemma3:1b") -> bool:
    try:
        import ollama
        models = ollama.list()
        available = [m.get("name", m.get("model", "")) for m in models.get("models", [])]
        return any(model.split(":")[0] in m for m in available)
    except Exception:
        return False


def get_available_ollama_models() -> list[str]:
    try:
        import ollama
        models = ollama.list()
        return [m.get("name", m.get("model", "")) for m in models.get("models", [])]
    except Exception:
        return []