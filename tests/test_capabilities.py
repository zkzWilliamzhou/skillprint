import os
import tempfile
import unittest

from skillprint import capabilities as caps


class DetectTests(unittest.TestCase):
    def test_known_capabilities_are_sorted_and_complete(self):
        names = caps.known_capabilities()
        self.assertEqual(names, sorted(names))
        for expected in ("file-read", "file-write", "network", "shell", "code-exec", "image-gen"):
            self.assertIn(expected, names)

    def test_detects_markers_with_file_line_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "run.py"), "w", encoding="utf-8") as handle:
                handle.write(
                    "import subprocess\n"
                    "subprocess.run(['ls'])\n"
                    "with open('x', 'r') as f: f.read()\n"
                )
            result = caps.detect(root)
            self.assertIn("shell", result)
            self.assertIn("file-read", result)
            evidence = result["shell"][0]
            self.assertEqual(evidence["file"], "run.py")
            self.assertEqual(evidence["line"], 2)
            self.assertIn("subprocess.run", evidence["text"])

    def test_no_markers_gives_empty_result(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "notes.txt"), "w", encoding="utf-8") as handle:
                handle.write("just some harmless notes\n")
            self.assertEqual(caps.detect(root), {})


if __name__ == "__main__":
    unittest.main()
