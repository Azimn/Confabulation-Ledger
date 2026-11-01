import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from replay_benchmark import replay


class BenchmarkTests(unittest.TestCase):
    def test_labeled_corpus_is_replayable(self):
        self.assertEqual(len(replay()), 12)


if __name__ == "__main__":
    unittest.main()
