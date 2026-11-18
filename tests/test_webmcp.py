import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WebMCPBehaviorTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the browser behavior harness")
    def test_webmcp_contracts_progressive_enhancement_and_rollback(self):
        completed = subprocess.run(
            ["node", str(ROOT / "tests" / "webmcp_harness.mjs")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout.strip())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["scenarios"], 3)
        self.assertEqual(result["tools"], ["search_policies", "get_policy"])


if __name__ == "__main__":
    unittest.main()
