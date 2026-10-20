import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ink import guard  # noqa: E402
from ink.guard import Guard  # noqa: E402


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.log = Path(self.dir.name) / "user_files" / "errors.log"
        self.notes = []
        self.guard = Guard(self.log, lambda: self.notes.append(1), "1.0.0")
        stderr = mock.patch("sys.stderr", io.StringIO())  # the guard prints tracebacks
        self.stderr = stderr.start()
        self.addCleanup(stderr.stop)

    def tearDown(self):
        self.dir.cleanup()

    def test_passes_results_through(self):
        @self.guard("fallback")
        def ok(a, b):
            return a + b

        self.assertEqual(ok(1, 2), 3)
        self.assertFalse(self.log.exists())
        self.assertEqual(self.notes, [])

    def test_error_returns_fallback_logs_and_notifies_once(self):
        @self.guard()
        def broken():
            raise ValueError("bad deck")

        self.assertIsNone(broken())
        self.assertIsNone(broken())
        log = self.log.read_text()
        self.assertEqual(log.count("Ink 1.0.0 in broken"), 2)
        self.assertIn("ValueError: bad deck", log)
        self.assertEqual(self.notes, [1])
        self.assertIn("ValueError: bad deck", self.stderr.getvalue())

    def test_fallback_function_gets_the_arguments(self):
        @self.guard(lambda handled, message: (True, message) if message == "mine" else handled)
        def on_message(handled, message):
            raise KeyError(message)

        self.assertEqual(on_message((False, None), "mine"), (True, "mine"))
        self.assertEqual(on_message((False, None), "theirs"), (False, None))

    def test_failing_fallback_and_notify_stay_contained(self):
        def notify():
            raise RuntimeError("no window")

        def fallback():
            raise RuntimeError("still broken")

        g = Guard(self.log, notify)

        @g(fallback)
        def broken():
            raise ValueError

        self.assertIsNone(broken())
        self.assertIn("in fallback", self.log.read_text())

    def test_unwritable_log_still_returns_fallback(self):
        self.log.parent.parent.joinpath("user_files").write_text("a file, not a folder")
        self.assertEqual(self.guard(7)(lambda: 1 / 0)(), 7)
        self.assertEqual(self.notes, [1])

    def test_log_starts_over_when_large(self):
        self.log.parent.mkdir()
        self.log.write_text("x" * (guard.MAX_LOG_BYTES + 1))
        self.guard()(lambda: 1 / 0)()
        self.assertTrue(self.log.read_text().startswith("20"))


if __name__ == "__main__":
    unittest.main()
