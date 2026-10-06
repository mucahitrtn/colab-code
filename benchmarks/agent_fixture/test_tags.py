import unittest
from tags import normalize_tags


class TagsTests(unittest.TestCase):
    def test_preserves_first_appearance(self):
        self.assertEqual(normalize_tags(['beta', 'alpha', 'beta']), ['beta', 'alpha'])

    def test_trims_before_deduplicating(self):
        self.assertEqual(normalize_tags([' alpha ', 'alpha', '\tbeta\n']), ['alpha', 'beta'])

    def test_skips_empty_tags(self):
        self.assertEqual(normalize_tags(['', '  ', 'beta', '\t']), ['beta'])

    def test_empty_input(self):
        self.assertEqual(normalize_tags([]), [])

    def test_preserves_case(self):
        self.assertEqual(normalize_tags(['Alpha', 'alpha', 'Alpha']), ['Alpha', 'alpha'])


if __name__ == '__main__':
    unittest.main()
