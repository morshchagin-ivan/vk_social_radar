from pathlib import Path
import unittest

class V041Tests(unittest.TestCase):
    def test_wheel_keyboard_extractor_present(self):
        from app import collector
        source = Path(collector.__file__).read_text(encoding="utf-8")
        self.assertIn("vk_reforged_exact_scroll_ancestor_v4", source)
        self.assertIn('mouse.wheel', source)
        self.assertIn('PageDown', source)

    def test_success_diagnostics_enabled(self):
        from app import collector
        source = Path(collector.__file__).read_text(encoding="utf-8")
        self.assertIn('_save_diagnostics("dialogs_success"', source)

if __name__ == "__main__":
    unittest.main()
