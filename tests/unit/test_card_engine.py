import sys
import unittest
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.card_engine import CardManager

class TestCardEngine(unittest.TestCase):
    def test_card_minting_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "test_cards.json"
            cm = CardManager(storage_path=tmp_file)
            
            self.assertEqual(cm.get_collection()["total_count"], 0)
            
            # Mint card
            card1 = cm.mint_card(memory_text="Test memory 1", force_rarity="rare")
            self.assertEqual(card1["rarity"], "rare")
            self.assertEqual(card1["memory_line"], "Test memory 1")
            self.assertEqual(cm.get_collection()["total_count"], 1)
            self.assertEqual(cm.get_collection()["showcase_id"], card1["id"])
            
            # Mint second card & set showcase
            card2 = cm.mint_card(memory_text="Test memory 2", force_rarity="legendary")
            self.assertEqual(card2["rarity"], "legendary")
            self.assertEqual(cm.get_collection()["total_count"], 2)
            
            success = cm.set_showcase(card2["id"])
            self.assertTrue(success)
            self.assertEqual(cm.get_collection()["showcase_id"], card2["id"])
            
            # Load from disk again to verify persistence
            cm2 = CardManager(storage_path=tmp_file)
            self.assertEqual(cm2.get_collection()["total_count"], 2)
            self.assertEqual(cm2.get_collection()["showcase_id"], card2["id"])

if __name__ == '__main__':
    unittest.main()
