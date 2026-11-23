"""Tests for core.lessons (study mode)."""
import asyncio
import json

import pytest

from core import lessons


def test_sanitize_op_clamps_and_filters():
    op = lessons.sanitize_op({"type": "box", "x": 500, "y": -5, "w": 9999, "h": "x", "text": "hi\n\x00", "color": "neon"})
    assert op["x"] == 100 and op["y"] == 0 and op["w"] == 100 and op["h"] == 12
    assert op["color"] == "ink" and op["text"] == "hi"
    assert lessons.sanitize_op({"type": "script", "x": 1}) is None
    assert lessons.sanitize_op({"type": "text", "x": 1, "y": 1, "text": ""}) is None
    assert lessons.sanitize_op("nope") is None


def test_parse_lesson_extracts_json_from_noise():
    raw = '<think>hmm</think>Sure! ```json\n' + json.dumps({
        "title": "Derivatives",
        "steps": [{"narration": "A derivative is a slope.", "draw": [
            {"type": "arrow", "x1": 10, "y1": 10, "x2": 50, "y2": 50},
            {"type": "bogus"}]},
            {"narration": "", "draw": []}],
    }) + "\n```"
    lesson = lessons.parse_lesson(raw)
    assert lesson["title"] == "Derivatives"
    assert len(lesson["steps"]) == 1
    assert len(lesson["steps"][0]["draw"]) == 1


@pytest.mark.parametrize("raw", ["", "⚠️ model down", "no json here", "{bad json}", '{"steps": []}'])
def test_parse_lesson_rejects_unusable(raw):
    with pytest.raises(ValueError):
        lessons.parse_lesson(raw)


def test_chunk_slides():
    assert lessons.chunk_slides(["a"] * 11) == [["a"] * 5, ["a"] * 5, ["a"]]


class FakeBrain:
    def __init__(self, replies):
        self.replies = list(replies)

    async def _call_llm(self, messages, **kwargs):
        assert kwargs.get("suppress_audio") is True
        return self.replies.pop(0)


GOOD = json.dumps({"title": "T", "steps": [{"narration": "Hello.", "draw": []}]})


def test_generate_lessons_skips_failed_groups():
    brain = FakeBrain([GOOD, "garbage"])
    result = asyncio.run(lessons.generate_lessons(brain, ["s"] * 6))
    assert len(result) == 1 and result[0]["slides"] == "1-5"


def test_generate_lessons_all_fail():
    with pytest.raises(ValueError):
        asyncio.run(lessons.generate_lessons(FakeBrain(["garbage"]), ["s"]))


def test_extract_slides_pptx(tmp_path):
    from pptx import Presentation
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Entropy"
    s.placeholders[1].text = "Disorder grows"
    prs.slides.add_slide(prs.slide_layouts[6])  # empty slide is dropped
    path = tmp_path / "a.pptx"
    prs.save(path)
    out = lessons.extract_slides(path)
    assert len(out) == 1 and "Entropy" in out[0]


def test_extract_slides_rejects_other_formats(tmp_path):
    with pytest.raises(ValueError):
        lessons.extract_slides(tmp_path / "x.docx")
