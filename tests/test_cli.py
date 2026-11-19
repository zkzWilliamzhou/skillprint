import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout

from skillprint.cli import EXIT_CHECK_FAILED, EXIT_OK, EXIT_USAGE_ERROR, main

DEMO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "demo_skill")
)


class CliTests(unittest.TestCase):
    def test_help_loads(self):
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, EXIT_OK)
        self.assertIn("skillprint", out.getvalue())

    def test_json_format_is_parseable(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([DEMO, "--format", "json"])
        self.assertEqual(code, EXIT_OK)
        data = json.loads(out.getvalue())
        self.assertEqual(data["name"], "demo-skill")

    def test_check_ok(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([DEMO, "--check", "--format", "json"])
        self.assertEqual(code, EXIT_OK)

    def test_bad_path_is_usage_error(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["/nonexistent/skillprint/path", "--format", "json"])
        self.assertEqual(code, EXIT_USAGE_ERROR)
        self.assertIn("error", err.getvalue().lower())

    def test_check_failure_exit_code(self):
        import shutil
        import tempfile

        root = tempfile.mkdtemp()
        try:
            with open(os.path.join(root, "SKILL.md"), "w", encoding="utf-8") as handle:
                handle.write("---\nname: risk\nallowed-tools: [read]\n---\nbody\n")
            with open(os.path.join(root, "script.py"), "w", encoding="utf-8") as handle:
                handle.write("subprocess.run(['ls'])\n")
            out = io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                code = main([root, "--check", "--format", "json"])
            self.assertEqual(code, EXIT_CHECK_FAILED)
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
