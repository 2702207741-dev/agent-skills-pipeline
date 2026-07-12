import unittest

from src.slugify import slugify


class SlugifyTests(unittest.TestCase):
    def test_words_are_normalized(self) -> None:
        self.assertEqual(slugify("  Agent Skills  "), "agent-skills")

    def test_empty_input_is_stable(self) -> None:
        self.assertEqual(slugify("   "), "")


if __name__ == "__main__":
    unittest.main()
