"""
Integration patch for Aiko's main.py
Add this to Aiko's startup sequence
"""

# Add to imports at top of main.py:
# from core.openclaw_launcher import integrate_with_aiko

# Add to AikoCore.__init__ or startup sequence:
# self.openclaw_launcher = integrate_with_aiko()

# Add to shutdown:
# if hasattr(self, 'openclaw_launcher') and self.openclaw_launcher:
#     self.openclaw_launcher.stop_bridge()

PATCH_CODE = '''
# OpenClaw Integration - Add to AikoCore.__init__
from core.openclaw_launcher import integrate_with_aiko

# ... existing init code ...

# Start OpenClaw bridge
self.openclaw_launcher = integrate_with_aiko()
if self.openclaw_launcher:
    self.logger.info("✅ OpenClaw bridge integrated")
else:
    self.logger.warning("⚠️ OpenClaw bridge not available")

# Add to shutdown method:
def shutdown(self):
    """Enhanced shutdown with OpenClaw cleanup"""
    # ... existing shutdown code ...
    
    # Stop OpenClaw bridge
    if hasattr(self, 'openclaw_launcher') and self.openclaw_launcher:
        self.openclaw_launcher.stop_bridge()
        self.logger.info("OpenClaw bridge stopped")
'''

print("=" * 60)
print("OpenClaw Integration Patch for Aiko")
print("=" * 60)
print()
print("Add the following to AikoCore.__init__ in main.py:")
print()
print(PATCH_CODE)
print()
print("=" * 60)
print("Or simply run: python core/openclaw_launcher.py")
print("to start the bridge independently.")
print("=" * 60)
