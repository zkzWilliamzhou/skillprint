import unittest

from skillprint.frontmatter import FrontmatterError, parse_frontmatter


class ParseFrontmatterTests(unittest.TestCase):
    def test_no_frontmatter_returns_empty(self):
        self.assertEqual(parse_frontmatter("# Just a doc\n"), {})

    def test_scalars_and_inline_list(self):
        text = (
            "---\n"
            "name: demo\n"
            'description: "A demo skill"\n'
            "version: 1.2.3\n"
            "allowed-tools: [read, write]\n"
            "---\n"
            "body\n"
        )
        data = parse_frontmatter(text)
        self.assertEqual(data["name"], "demo")
        self.assertEqual(data["description"], "A demo skill")
        self.assertEqual(data["version"], "1.2.3")
        self.assertEqual(data["allowed-tools"], ["read", "write"])

    def test_block_list(self):
        text = (
            "---\n"
            "allowed-tools:\n"
            "  - shell\n"
            "  - network\n"
            "---\n"
        )
        self.assertEqual(parse_frontmatter(text)["allowed-tools"], ["shell", "network"])

    def test_unclosed_block_raises(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\nname: broken\n")

    def test_invalid_line_raises(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\njust a line\n---\n")


if __name__ == "__main__":
    unittest.main()
