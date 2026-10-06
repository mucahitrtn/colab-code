import unittest
from client.model_limits import model_budgets

class BudgetTests(unittest.TestCase):
    def test_reserves_output_at_each_supported_size(self):
        for length in (32768, 65536, 131072, 262144):
            with self.subTest(length=length):
                result = model_budgets({'data': [{'id': 'qwen', 'max_model_len': length}]}, 'qwen')
                self.assertEqual(result['contextWindow'] + result['maxTokens'], length)
                self.assertEqual(result['maxTokens'], 8192)

    def test_requires_requested_model(self):
        with self.assertRaises(ValueError):
            model_budgets({'data': [{'id': 'other', 'max_model_len': 32768}]}, 'qwen')

    def test_rejects_missing_or_invalid_limit(self):
        for value in (None, True, '131072', 0, 8192):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model_budgets({'data': [{'id': 'qwen', 'max_model_len': value}]}, 'qwen')

if __name__ == '__main__':
    unittest.main()
