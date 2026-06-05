# Application Notes for Open-Source Maintainer Programs

This document is optional. Edit it before applying anywhere.

## Short project summary

`oss-triage-reporter` is a lightweight CLI and GitHub Action for small open-source maintainers. It generates markdown reports for issue triage, pull request review context, changelog drafting, and CI failure summaries.

## Why this project matters

Many small open-source projects are maintained by one person or a small volunteer group. These maintainers often need to review issues, pull requests, release notes, and CI failures without a dedicated project management system. This tool keeps the workflow simple: run one CLI command or scheduled GitHub Action and get a readable markdown report.

## Maintainer role

Replace this section with your real role. Example:

I am the primary maintainer of this repository. I created the project, review issues and pull requests, publish releases, and maintain the GitHub Action workflow.

## Evidence to collect before applying

- Public GitHub repository link.
- Clear README and license.
- At least one tagged release.
- Passing CI badge.
- Real example report generated from the repository.
- A few issues or pull requests showing active maintenance.
- Stars, forks, downloads, or downstream usage if available.

## Honest limitations

The first version uses deterministic heuristics rather than an LLM. This keeps it safe, low-cost, and easy to run in public repositories. Future versions may optionally support local or hosted model providers for richer summaries.
