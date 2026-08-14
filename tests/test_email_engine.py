import unittest
import asyncio
from core.email_engine import EmailEngine, email_engine
from core.config_manager import config

class TestEmailEngine(unittest.TestCase):
    def test_email_engine_initialization(self):
        engine = EmailEngine()
        self.assertIsNotNone(engine)
        self.assertIsInstance(engine.enabled, bool)

    def test_email_settings_config(self):
        email_cfg = config.get("email") or {}
        self.assertIsInstance(email_cfg, dict)

if __name__ == "__main__":
    unittest.main()
