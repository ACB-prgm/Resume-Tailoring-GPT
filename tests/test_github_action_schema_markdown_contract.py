from __future__ import annotations

import json
from pathlib import Path
import unittest


class GithubActionSchemaMarkdownContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.schema = json.loads((self.repo_root / "github_action_schema.json").read_text(encoding="utf-8"))

    def test_create_git_tree_path_pattern_is_markdown(self) -> None:
        pattern = (
            self.schema["components"]["schemas"]["CreateGitTreeRequest"]["properties"]["tree"]["items"]["properties"]["path"]["pattern"]
        )
        self.assertEqual(
            pattern,
            "^CareerCorpus\\/(profile|experience|projects|certifications|education)\\.md$",
        )
        self.assertNotIn("metadata", pattern)
        self.assertNotIn(".json", pattern)

    def test_blob_accept_headers_remain_raw(self) -> None:
        get_blob_params = self.schema["paths"]["/repos/{owner}/career-corpus-memory/git/blobs/{blob_sha}"]["get"]["parameters"]
        post_blob_params = self.schema["paths"]["/repos/{owner}/career-corpus-memory/git/blobs"]["post"]["parameters"]

        get_accept = [p for p in get_blob_params if p.get("name") == "Accept"][0]
        post_accept = [p for p in post_blob_params if p.get("name") == "Accept"][0]

        self.assertEqual(get_accept["schema"]["const"], "application/vnd.github.raw")
        self.assertEqual(post_accept["schema"]["const"], "application/vnd.github.raw")


if __name__ == "__main__":
    unittest.main()
