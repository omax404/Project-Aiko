import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import MagicMock, AsyncMock, patch
from core.proactive import ProactiveAgent, GREETINGS

@pytest.fixture
def mock_agent_deps():
    brain = MagicMock()
    brain.chat = AsyncMock(return_value=("Hi!", "happy"))
    brain.ask_raw = AsyncMock(return_value="Nice song!")
    
    vision = MagicMock()
    vision.scan_screen = AsyncMock(return_value=("User is browsing", MagicMock()))
    
    pc = MagicMock()
    voice = MagicMock()
    voice.speak = AsyncMock(return_value="audio_file.wav")
    
    obsidian = MagicMock()
    obsidian.is_valid = True
    obsidian.get_daily_note_content.return_value = "- [ ] Finish pytest suite\n- [x] Drink tea"
    
    return brain, vision, pc, voice, obsidian

def test_proactive_agent_initialization(mock_agent_deps):
    brain, vision, pc, voice, obsidian = mock_agent_deps
    agent = ProactiveAgent(brain, vision, pc, voice, obsidian)
    assert agent.brain == brain
    assert agent.vision == vision
    assert agent.pc == pc
    assert agent.voice == voice
    assert agent.obsidian == obsidian
    assert agent.active is False

@pytest.mark.asyncio
async def test_maybe_greet_morning(mock_agent_deps):
    brain, vision, pc, voice, obsidian = mock_agent_deps
    agent = ProactiveAgent(brain, vision, pc, voice, obsidian)
    agent._send_proactive = AsyncMock()
    
    # Morning: 7–9 AM
    morning_time = datetime(2026, 6, 27, 8, 30)
    await agent._maybe_greet(morning_time)
    
    agent._send_proactive.assert_called_once()
    args, kwargs = agent._send_proactive.call_args
    assert args[0] in GREETINGS["morning"]
    assert args[1] == "excited"

@pytest.mark.asyncio
async def test_maybe_greet_evening(mock_agent_deps):
    brain, vision, pc, voice, obsidian = mock_agent_deps
    agent = ProactiveAgent(brain, vision, pc, voice, obsidian)
    agent._send_proactive = AsyncMock()
    
    # Evening: 18–20 PM (requires morning greet date match but hour < 18)
    agent.last_greeting_date = date(2026, 6, 27)
    agent.last_greeting_hour = 8
    evening_time = datetime(2026, 6, 27, 19, 0)
    await agent._maybe_greet(evening_time)
    
    agent._send_proactive.assert_called_once()
    args, kwargs = agent._send_proactive.call_args
    assert args[0] in GREETINGS["evening"]
    assert args[1] == "happy"

def test_toggle(mock_agent_deps):
    brain, vision, pc, voice, obsidian = mock_agent_deps
    agent = ProactiveAgent(brain, vision, pc, voice, obsidian)
    
    assert agent.toggle(True) is True
    assert agent.active is True
    assert agent.toggle(False) is False
    assert agent.active is False

@pytest.mark.asyncio
async def test_check_obsidian_tasks(mock_agent_deps):
    brain, vision, pc, voice, obsidian = mock_agent_deps
    agent = ProactiveAgent(brain, vision, pc, voice, obsidian)
    agent._send_proactive = AsyncMock()
    
    now = datetime.now()
    await agent._check_obsidian_tasks(now)
    
    obsidian.get_daily_note_content.assert_called_once()
    brain.chat.assert_called_once()
    agent._send_proactive.assert_called_once()
