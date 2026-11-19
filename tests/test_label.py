import json
import os
import shutil
import tempfile
import unittest

from skillprint.label import LabelError, check, load_skill, render

DEMO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "demo_skill")
)


def make_skill(frontmatter, body="", script=None):
    root = tempfile.mkdtemp()
    with open(os.path.join(root, "SKILL.md"), "w", encoding="utf-8") as handle:
        handle.write("---\n" + frontmatter + "\n---\n" + body)
    if script is not None:
        with open(os.path.join(root, "script.py"), "w", encoding="utf-8") as handle:
            handle.write(script)
    return root


class LabelTests(unittest.TestCase):
    def test_demo_skill_loads_and_checks_clean(self):
        label = load_skill(DEMO)
        self.assertEqual(label["name"], "demo-skill")
        self.assertEqual(label["version"], "1.0.0")
        self.assertTrue(label["capabilities"]["shell"]["detected"])
        self.assertEqual(check(label), [])

    def test_json_render_is_deterministic_and_sorted(self):
        label = load_skill(DEMO)
        first = render(label, "json")
        second = render(json.loads(first), "json")
        self.assertEqual(first, second)
        self.assertEqual(first, json.dumps(json.loads(first), indent=2, sort_keys=True, ensure_ascii=False))

    def test_text_render_contains_header(self):
        text = render(load_skill(DEMO), "text")
        self.assertIn("Capability label: demo-skill", text)
        self.assertIn("CAPABILITIES", text)

    def test_missing_skill_dir_raises(self):
        with self.assertRaises(LabelError):
            load_skill(os.path.join(tempfile.gettempdir(), "does-not-exist-skillprint"))

    def test_missing_skill_md_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(LabelError):
                load_skill(root)

    def test_undeclared_dangerous_marker_fails_check(self):
        root = make_skill(
            "name: risk\nversion: 1.0.0\nallowed-tools: [read]\n",
            body="runs a shell command\n",
            script="subprocess.run(['ls'])\n",
        )
        try:
            label = load_skill(root)
            failures = check(label)
            self.assertTrue(any("dangerous capability 'shell'" in f for f in failures))
        finally:
            shutil.rmtree(root)

    def test_declared_but_undocumented_capability_fails_check(self):
        root = make_skill(
            "name: liar\nversion: 1.0.0\ncapabilities: [image-gen]\n",
            body="does nothing image related\n",
        )
        try:
            label = load_skill(root)
            failures = check(label)
            self.assertTrue(any("declared but not documented" in f for f in failures))
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
