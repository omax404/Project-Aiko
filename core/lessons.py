"""
core/lessons.py

Study mode: turn lecture slides (PDF / PPTX) into short, gentle lessons that the
desktop app draws live on a board while Aiko's voice walks through each step.

Pipeline: extract text per slide -> ask the LLM for a JSON lesson per slide group
-> validate and clamp every drawing instruction so the client can render it safely.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("Lessons")

MAX_SLIDES = 40
SLIDES_PER_LESSON = 5
MAX_STEPS = 8
MAX_OPS_PER_STEP = 8
MAX_TEXT = 90
MAX_NARRATION = 600
COLORS = {"ink", "red", "blue", "green", "gold", "purple"}
OP_TYPES = {"text", "box", "circle", "arrow", "line"}
SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}


def extract_slides(path: Path) -> List[str]:
    """Return the text of each slide/page. Empty pages are dropped."""
    ext = Path(path).suffix.lower()
    slides: List[str] = []
    if ext == ".pdf":
        from pypdf import PdfReader
        for page in PdfReader(str(path)).pages[:MAX_SLIDES * 2]:
            slides.append((page.extract_text() or "").strip())
    elif ext == ".pptx":
        from pptx import Presentation
        for slide in Presentation(str(path)).slides:
            parts = []
            for shape in slide.shapes:
                if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                    parts.append(shape.text_frame.text.strip())
            slides.append("\n".join(parts))
    else:
        raise ValueError(f"Unsupported slide format '{ext}'. Use PDF or PPTX.")
    return [s for s in slides if s][:MAX_SLIDES]


def chunk_slides(slides: List[str], size: int = SLIDES_PER_LESSON) -> List[List[str]]:
    return [slides[i:i + size] for i in range(0, len(slides), size)]


def build_prompt(chunk: List[str], index: int, total: int) -> List[Dict[str, str]]:
    slide_text = "\n\n".join(f"[Slide {i + 1}]\n{t[:1500]}" for i, t in enumerate(chunk))
    system = (
        "You are Aiko, a warm, patient tutor. Slides often don't make sense on their own, "
        "so you re-explain them as a short, gentle lesson drawn on a whiteboard while you talk. "
        "Reply with ONLY JSON, no prose, in this shape:\n"
        '{"title": str, "steps": [{"narration": str, "draw": [op, ...]}]}\n'
        f"Use 3 to {MAX_STEPS} steps. Narration is 1-3 plain spoken sentences, no markdown or emoji. "
        "The board is a 100x100 grid (x right, y down). Each op is one of:\n"
        '{"type":"text","x":n,"y":n,"text":str,"color":c}\n'
        '{"type":"box","x":n,"y":n,"w":n,"h":n,"text":str,"color":c}\n'
        '{"type":"circle","x":n,"y":n,"r":n,"text":str,"color":c}\n'
        '{"type":"arrow","x1":n,"y1":n,"x2":n,"y2":n,"color":c}\n'
        '{"type":"line","x1":n,"y1":n,"x2":n,"y2":n,"color":c}\n'
        f"color is one of {sorted(COLORS)}. Keep drawings sparse and short labels (under {MAX_TEXT} chars). "
        "Define terms, give one intuition or example, and build up step by step."
    )
    user = f"Lesson {index + 1} of {total}. Teach these slides:\n\n{slide_text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _num(value: Any, default: float = 0.0, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if n != n:  # NaN
        return default
    return max(lo, min(hi, n))


def _clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value or "")).strip()
    return text[:limit]


def sanitize_op(op: Any):
    """Validate one drawing instruction. Returns a clean dict or None."""
    if not isinstance(op, dict) or op.get("type") not in OP_TYPES:
        return None
    kind = op["type"]
    color = op.get("color") if op.get("color") in COLORS else "ink"
    out: Dict[str, Any] = {"type": kind, "color": color}
    if kind in ("arrow", "line"):
        for k in ("x1", "y1", "x2", "y2"):
            out[k] = _num(op.get(k))
        return out
    out["x"], out["y"] = _num(op.get("x")), _num(op.get("y"))
    out["text"] = _clean_text(op.get("text"), MAX_TEXT)
    if kind == "text":
        if not out["text"]:
            return None
    elif kind == "box":
        out["w"] = _num(op.get("w"), 20, 2, 100)
        out["h"] = _num(op.get("h"), 12, 2, 100)
    elif kind == "circle":
        out["r"] = _num(op.get("r"), 8, 1, 50)
    return out


def parse_lesson(raw: str) -> Dict[str, Any]:
    """Parse and sanitize the model's reply. Raises ValueError if unusable."""
    if not raw or raw.lstrip().startswith("⚠️"):
        raise ValueError(raw or "empty model reply")
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model reply contained no JSON")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"model reply was not valid JSON: {e}") from e
    steps = []
    for step in (data.get("steps") or [])[:MAX_STEPS]:
        if not isinstance(step, dict):
            continue
        narration = _clean_text(step.get("narration"), MAX_NARRATION)
        if not narration:
            continue
        ops = [o for o in (sanitize_op(x) for x in (step.get("draw") or [])[:MAX_OPS_PER_STEP]) if o]
        steps.append({"narration": narration, "draw": ops})
    if not steps:
        raise ValueError("lesson had no usable steps")
    return {"title": _clean_text(data.get("title"), 80) or "Lesson", "steps": steps}


async def generate_lessons(brain, slides: List[str]) -> List[Dict[str, Any]]:
    """Generate one lesson per slide group. Groups the model fails on are skipped."""
    chunks = chunk_slides(slides)
    lessons: List[Dict[str, Any]] = []
    last_error = ""
    for i, chunk in enumerate(chunks):
        try:
            raw = await brain._call_llm(build_prompt(chunk, i, len(chunks)), suppress_audio=True)
            lesson = parse_lesson(raw)
            lesson["slides"] = f"{i * SLIDES_PER_LESSON + 1}-{i * SLIDES_PER_LESSON + len(chunk)}"
            lessons.append(lesson)
        except Exception as e:  # one bad group must not lose the whole deck
            last_error = str(e)
            logger.warning(f"[Lessons] group {i + 1}/{len(chunks)} failed: {e}")
    if not lessons:
        raise ValueError(last_error or "could not build any lessons")
    return lessons
