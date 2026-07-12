import unittest

from src.release_notes import release_heading


class ReleaseHeadingTests(unittest.TestCase):
    def test_first_change_is_normalized(self) -> None:
        self.assertEqual(release_heading(["  Added audit export  "]), "## Added audit export")

    def test_empty_changes_are_stable(self) -> None:
        self.assertEqual(release_heading([]), "## No user-facing changes")


if __name__ == "__main__":
    unittest.main()
