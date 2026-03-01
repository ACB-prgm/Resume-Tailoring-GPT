from __future__ import annotations

import unittest
from pathlib import Path


class RouterCutoverContractTests(unittest.TestCase):
    """Test suite for router cutover contract."""
    def test_instructions_are_router_first(self) -> None:
        """Test that instructions are router first."""
        path = Path(__file__).resolve().parents[1] / "instructions.txt"
        text = path.read_text(encoding="utf-8")

        self.assertIn("intent_context_router_surface.py", text)
        self.assertIn("build_context", text)
        self.assertIn("Runtime dependency model is atoms-only", text)
        self.assertNotIn("resolve_intent", text)

        self.assertNotIn("Reference Pack", text)
        self.assertNotIn("$Ref:", text)
        self.assertNotIn("Intent Matrix", text)


if __name__ == "__main__":
    unittest.main()
