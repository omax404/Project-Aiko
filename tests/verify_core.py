
import asyncio
import os
import sys
from pathlib import Path

# Fix path to include core
sys.path.append(str(Path(__file__).parent.parent))

async def test_security():
    print("--- Testing Security Manager Authorization ---")
    from core.security import policy_engine
    
    # Test 1: Desktop Master should be admin
    print(f"Testing 'Master': {'SUCCESS' if policy_engine.is_admin('Master') else 'FAILED'}")
    
    # Test 2: Random user should NOT be admin
    print(f"Testing 'Stranger123': {'FAILED - Allowed' if policy_engine.is_admin('Stranger123') else 'SUCCESS - Blocked'}")
    
    # Test 3: Admin IDs from .env (mocking env for test)
    os.environ["ADMIN_IDS"] = "999,888"
    print(f"Testing Whitelisted '999': {'SUCCESS' if policy_engine.is_admin('999') else 'FAILED'}")
    print(f"Testing Non-Whitelisted '777': {'FAILED - Allowed' if policy_engine.is_admin('777') else 'SUCCESS - Blocked'}")

async def test_voice():
    print("\n--- Testing Voice Engine (Edge-TTS) ---")
    try:
        from core.voice import voice_engine
        # Just check if we can synthesize a tiny snippet without full playback
        # We'll just verify the call doesn't crash
        print("Initializing Edge-TTS...")
        # Speak small text, but we'll mock the internal file writing or just let it run if it's fast
        # (Assuming internet is available for edge-tts)
        print("Synthesizing test phrase...")
        # Note: we are not testing audio output device here, just the generation pipeline
        success = await voice_engine.speak("Testing system integrity.", emotion="happy")
        print(f"Voice generation: SUCCESS")
    except Exception as e:
        print(f"Voice generation: FAILED - {e}")

async def test_brain_tools():
    print("\n--- Testing Brain Tool Blocking ---")
    from unittest.mock import MagicMock
    from core.chat_engine import AikoBrain
    
    # Mock dependencies
    mem = MagicMock()
    rag = MagicMock()
    brain = AikoBrain(mem, rag)
    
    observations = []
    images = []
    
    # Test: Stranger trying to use [OPEN:]
    print("Simulating Stranger attempting [OPEN: notepad]...")
    await brain._execute_tools("[OPEN: notepad]", observations, images, user_id="Stranger")
    
    found_block = any("Security Block" in obs for obs in observations)
    if found_block:
        print("Result: SUCCESS - Unauthorized [OPEN] was blocked.")
    else:
        print(f"Result: FAILED - Command was not blocked! Observations: {observations}")

    observations = []
    # Test: Master trying to use [OPEN:]
    print("Simulating Master attempting [OPEN: notepad]...")
    # NOTE: This might actually try to open notepad on the runner if we don't mock os.system
    # For safe test, we just check if it DOES NOT have the Security Block
    # We briefly mock os.system to avoid actually popping notepad during the test
    import os
    orig_system = os.system
    os.system = MagicMock(return_value=0)
    
    await brain._execute_tools("[OPEN: notepad]", observations, images, user_id="Master")
    found_block = any("Security Block" in obs for obs in observations)
    
    os.system = orig_system # Restore
    
    if not found_block:
        print("Result: SUCCESS - Authorized [OPEN] was permitted.")
    else:
        print(f"Result: FAILED - Authorized command was blocked! Observations: {observations}")

async def main():
    await test_security()
    await test_brain_tools()
    # Skip voice test in this env if internet is restricted or edge-tts is missing
    # await test_voice()

if __name__ == "__main__":
    asyncio.run(main())
