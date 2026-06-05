import unittest

from oss_triage_reporter.reports import (
    classify_changelog_item,
    classify_issue,
    clean_title,
    make_changelog_report,
    make_issue_triage_report,
    summarize_log,
)


class ReportTests(unittest.TestCase):
    def test_classifies_bug_with_missing_repro(self):
        issue = {
            "number": 42,
            "title": "Crash when opening config file",
            "body": "The app crashes on startup.",
            "labels": [],
        }
        result = classify_issue(issue)
        self.assertEqual(result["category"], "bug")
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["needs_info"], "yes")
        self.assertIn("needs-repro", result["suggested_labels"])

    def test_classifies_feature_request(self):
        issue = {
            "number": 7,
            "title": "Add CSV export support",
            "body": "It would help reporting workflows.",
            "labels": [{"name": "enhancement"}],
        }
        result = classify_issue(issue)
        self.assertEqual(result["category"], "feature")
        self.assertEqual(result["priority"], "low")

    def test_changelog_classification(self):
        pr = {
            "title": "fix: handle empty input",
            "body": "",
            "labels": [],
        }
        self.assertEqual(classify_changelog_item(pr), "Fixed")
        self.assertEqual(clean_title("feat(parser): add config loader"), "Add config loader")

    def test_log_summary_extracts_relevant_lines(self):
        log = "ok\nTraceback most recent call last\nModuleNotFoundError: No module named 'x'\ndone"
        result = summarize_log(log)
        self.assertEqual(len(result), 2)
        self.assertIn("Traceback", result[0])
        self.assertIn("ModuleNotFoundError", result[1])

    def test_markdown_reports_are_generated(self):
        issues = [
            {
                "number": 1,
                "title": "Documentation typo",
                "body": "README typo",
                "html_url": "https://example.com/1",
                "labels": [{"name": "documentation"}],
            }
        ]
        report = make_issue_triage_report("owner/repo", issues)
        self.assertIn("Issue Triage Report", report)
        self.assertIn("Documentation", report)

        prs = [
            {
                "number": 2,
                "title": "feat: add JSON output",
                "body": "",
                "html_url": "https://example.com/2",
                "labels": [{"name": "enhancement"}],
                "user": {"login": "alice"},
            }
        ]
        changelog = make_changelog_report("owner/repo", prs, days=30)
        self.assertIn("Changelog Draft", changelog)
        self.assertIn("JSON output", changelog)


if __name__ == "__main__":
    unittest.main()
