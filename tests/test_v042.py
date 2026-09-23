from pathlib import Path
import unittest

class V042Tests(unittest.TestCase):
    def test_exact_scroll_ancestor_extractor(self):
        from app import collector
        source = Path(collector.__file__).read_text(encoding="utf-8")
        self.assertIn("vk_reforged_exact_scroll_ancestor_v4", source)
        self.assertIn("ancestor_chain", source)
        self.assertIn("first_key", source)
        self.assertIn("last_key", source)

    def test_small_wheel_steps(self):
        from app import collector
        source = Path(collector.__file__).read_text(encoding="utf-8")
        self.assertIn("for _ in range(8)", source)
        self.assertIn("mouse.wheel(0, 360)", source)

if __name__ == "__main__":
    unittest.main()
