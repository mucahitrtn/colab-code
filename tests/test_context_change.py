import unittest
from colab.reconfigure import has_active_requests, validate_length

class ContextChangeTests(unittest.TestCase):
    def test_accepts_custom_sizes_within_native_limit(self):
        for length in (16384, 48000, 65536, 131072, 262144):
            validate_length(length, 262144)

    def test_rejects_outside_native_limit(self):
        for length in (True, '65536', 16383, 262145):
            with self.subTest(length=length), self.assertRaises(ValueError):
                validate_length(length, 262144)
        with self.assertRaises(ValueError):
            validate_length(131072, 65536)

    def test_running_or_queued_requests_prevent_restart(self):
        for running, waiting in ((1,0), (0,1), (1,1)):
            metrics = f'vllm:num_requests_running{{engine="0"}} {running}\nvllm:num_requests_waiting{{engine="0"}} {waiting}'
            self.assertTrue(has_active_requests(metrics))

    def test_idle_is_allowed(self):
        self.assertFalse(has_active_requests('vllm:num_requests_running{engine="0"} 0.0\nvllm:num_requests_waiting{engine="0"} 0.0'))

    def test_unknown_metrics_prevent_restart(self):
        with self.assertRaises(ValueError):
            has_active_requests('# request counters unavailable')

if __name__ == '__main__':
    unittest.main()
