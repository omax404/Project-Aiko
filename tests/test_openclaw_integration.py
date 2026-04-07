"""
Test script for OpenClaw integration
Run this to verify everything is working
"""

import asyncio
import sys
from pathlib import Path

# Add Aiko to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_bridge():
    """Test the OpenClaw bridge"""
    print("🧪 Testing OpenClaw Integration")
    print("=" * 50)
    
    # Test 1: Import modules
    print("\n1️⃣ Testing imports...")
    try:
        from core.openclaw_bridge_enhanced import OpenClawBridge
        from core.clawdbot_bridge import ClawdbotBridge, get_bridge
        from skills.openclaw import OpenClawSkill
        print("   ✅ All modules imported successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Create bridge instances
    print("\n2️⃣ Creating bridge instances...")
    try:
        bridge = OpenClawBridge()
        clawd = ClawdbotBridge()
        skill = OpenClawSkill()
        print("   ✅ Bridge instances created")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Check workspace
    print("\n3️⃣ Checking workspace...")
    try:
        workspace = Path("~/clawd").expanduser()
        if workspace.exists():
            print(f"   ✅ Workspace exists: {workspace}")
        else:
            print(f"   ⚠️  Workspace not found: {workspace}")
            print("   Creating workspace...")
            workspace.mkdir(parents=True, exist_ok=True)
            print("   ✅ Workspace created")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 4: Check memory directory
    print("\n4️⃣ Checking memory directory...")
    try:
        memory_dir = workspace / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Memory directory ready: {memory_dir}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 5: Test file operations
    print("\n5️⃣ Testing file operations...")
    try:
        test_content = "OpenClaw integration test"
        await skill.write_file("test_openclaw.txt", test_content)
        read_content = await skill.read_file("test_openclaw.txt")
        
        if read_content == test_content:
            print("   ✅ File operations working")
        else:
            print(f"   ⚠️  Content mismatch: {read_content}")
        
        # Cleanup
        test_file = workspace / "test_openclaw.txt"
        if test_file.exists():
            test_file.unlink()
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 6: Check OpenClaw CLI
    print("\n6️⃣ Checking OpenClaw CLI...")
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✅ OpenClaw available: {result.stdout.strip()}")
        else:
            print(f"   ⚠️  OpenClaw check failed: {result.stderr}")
    except Exception as e:
        print(f"   ⚠️  OpenClaw not found: {e}")
        print("   Install with: npm install -g openclaw")
    
    # Test 7: Check coding agents
    print("\n7️⃣ Checking coding agents...")
    agents = {
        "codex": ["codex", "--version"],
        "claude": ["claude", "--version"]
    }
    
    for name, cmd in agents.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {name} available")
            else:
                print(f"   ⚠️  {name} not available")
        except:
            print(f"   ⚠️  {name} not installed")
    
    print("\n" + "=" * 50)
    print("✅ Integration test complete!")
    print("\nNext steps:")
    print("1. Start the bridge: python core/openclaw_launcher.py")
    print("2. Test delegation: python tests/test_openclaw_delegation.py")
    print("3. Use in Aiko: from skills.openclaw import code")
    
    return True


async def test_delegation():
    """Test actual task delegation (requires bridge running)"""
    print("\n🚀 Testing Task Delegation")
    print("=" * 50)
    
    from skills.openclaw import code, research
    
    # Test simple coding task
    print("\n1️⃣ Testing simple coding task...")
    try:
        result = await code("Write a Python function to calculate fibonacci numbers")
        print(f"   Status: {result.get('status', 'unknown')}")
        if result.get('status') == 'completed':
            print("   ✅ Task delegation working!")
        else:
            print(f"   ⚠️  Result: {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print("   Make sure the bridge is running: python core/openclaw_launcher.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenClaw integration")
    parser.add_argument("--full", action="store_true", help="Run full tests including delegation")
    args = parser.parse_args()
    
    # Run basic tests
    success = asyncio.run(test_bridge())
    
    # Run delegation tests if requested
    if args.full and success:
        asyncio.run(test_delegation())
