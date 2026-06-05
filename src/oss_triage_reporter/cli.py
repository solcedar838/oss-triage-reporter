from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from .github import GitHubClient, GitHubError, Repository, newer_than_iso
from .reports import (
    make_changelog_report,
    make_ci_report,
    make_issue_triage_report,
    make_weekly_report,
    summarize_log,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="osskit",
        description="Generate lightweight GitHub maintainer reports for small open-source projects.",
    )
    parser.add_argument("--token", help="GitHub token. Defaults to GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--api-url", default="https://api.github.com", help="GitHub API URL, useful for GitHub Enterprise.")
    sub = parser.add_subparsers(dest="command", required=True)

    triage = sub.add_parser("triage", help="Summarize open issues into a maintainer triage report.")
    triage.add_argument("repo", help="Repository in owner/repo format or a GitHub URL.")
    triage.add_argument("--limit", type=int, default=50, help="Maximum open issues to inspect.")
    triage.add_argument("--output", "-o", help="Write markdown output to this file.")

    changelog = sub.add_parser("changelog", help="Generate a changelog draft from recently merged PRs.")
    changelog.add_argument("repo", help="Repository in owner/repo format or a GitHub URL.")
    changelog.add_argument("--days", type=int, default=30, help="Merged PR lookback window.")
    changelog.add_argument("--limit", type=int, default=100, help="Maximum closed PRs to inspect.")
    changelog.add_argument("--output", "-o", help="Write markdown output to this file.")

    ci = sub.add_parser("ci-summary", help="Summarize recent failed GitHub Actions runs.")
    ci.add_argument("repo", help="Repository in owner/repo format or a GitHub URL.")
    ci.add_argument("--limit", type=int, default=3, help="Maximum failed runs to inspect.")
    ci.add_argument("--include-logs", action="store_true", help="Download workflow logs and extract error signals.")
    ci.add_argument("--output", "-o", help="Write markdown output to this file.")

    weekly = sub.add_parser("weekly-report", help="Generate one combined issue, changelog, and CI report.")
    weekly.add_argument("repo", help="Repository in owner/repo format or a GitHub URL.")
    weekly.add_argument("--days", type=int, default=7, help="Merged PR lookback window.")
    weekly.add_argument("--issue-limit", type=int, default=50, help="Maximum open issues to inspect.")
    weekly.add_argument("--pr-limit", type=int, default=100, help="Maximum closed PRs to inspect.")
    weekly.add_argument("--run-limit", type=int, default=3, help="Maximum failed CI runs to inspect.")
    weekly.add_argument("--output", "-o", help="Write markdown output to this file.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = GitHubClient(token=args.token, api_url=args.api_url)

    try:
        repo = Repository.parse(args.repo)
        if args.command == "triage":
            issues = client.open_issues(repo, limit=args.limit)
            text = make_issue_triage_report(repo.slug, issues)
        elif args.command == "changelog":
            prs = [pr for pr in client.merged_pulls(repo, limit=args.limit) if newer_than_iso(pr.get("merged_at"), args.days)]
            text = make_changelog_report(repo.slug, prs, args.days)
        elif args.command == "ci-summary":
            runs = client.failed_runs(repo, limit=args.limit)
            log_summaries = {}
            if args.include_logs:
                for run in runs:
                    run_id = int(run.get("id", 0))
                    try:
                        log_summaries[run_id] = summarize_log(client.run_log_text(repo, run_id))
                    except GitHubError as exc:
                        log_summaries[run_id] = [f"Could not collect logs: {exc}"]
            text = make_ci_report(repo.slug, runs, log_summaries)
        elif args.command == "weekly-report":
            issues = client.open_issues(repo, limit=args.issue_limit)
            prs = [pr for pr in client.merged_pulls(repo, limit=args.pr_limit) if newer_than_iso(pr.get("merged_at"), args.days)]
            runs = client.failed_runs(repo, limit=args.run_limit)
            text = make_weekly_report(repo.slug, issues, prs, runs, args.days)
        else:
            parser.error(f"Unknown command: {args.command}")
            return 2
    except (GitHubError, ValueError) as exc:
        print(f"osskit: {exc}", file=sys.stderr)
        return 1

    write_output(text, getattr(args, "output", None))
    return 0


def write_output(text: str, output: str | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    raise SystemExit(main())
