from __future__ import annotations

import unittest


class V031Tests(unittest.TestCase):
    def test_new_extractor_marker_exists(self):
        from app import collector
        source = open(collector.__file__, "r", encoding="utf-8").read()
        self.assertIn("profile_virtualized_accumulator_v2", source)

    def test_extended_vk_cdn_whitelist(self):
        from app.collector import ALLOWED_HOST_SUFFIXES
        self.assertIn("vkcdn.ru", ALLOWED_HOST_SUFFIXES)
        self.assertIn("vkvideo.ru", ALLOWED_HOST_SUFFIXES)

    def test_old_document_only_extractor_removed(self):
        from app import collector
        source = open(collector.__file__, "r", encoding="utf-8").read()
        self.assertNotIn("profile_anchor_v1", source)


if __name__ == "__main__":
    unittest.main()
