# OSS Triage Reporter

A lightweight CLI and GitHub Action for small open-source maintainers to summarize issues, pull requests, changelog drafts, and CI failures.

> This project is intentionally small. It is designed for maintainers who want useful markdown reports without running a database, dashboard, or hosted service.

## What it does

`oss-triage-reporter` helps maintainers answer recurring questions:

- Which open issues need triage?
- Which issues look like bugs, feature requests, docs requests, or questions?
- Which issues are missing reproduction details?
- What changed recently and can be turned into release notes?
- Which GitHub Actions runs failed recently?

It outputs plain Markdown that can be copied into issues, pull requests, release notes, or weekly maintainer updates.

## Features

- `osskit triage`: groups open issues and suggests labels, priority, and maintainer follow-up.
- `osskit changelog`: creates a changelog draft from recently merged pull requests.
- `osskit ci-summary`: summarizes recent failed GitHub Actions runs.
- `osskit weekly-report`: combines issue triage, changelog, and CI failure summaries.
- GitHub Action support for scheduled weekly reports.
- No runtime dependencies beyond the Python standard library.

## Installation

### From a local checkout

```bash
git clone https://github.com/solcedar838/oss-triage-reporter.git
cd oss-triage-reporter
python -m pip install -e .
```

Then run:

```bash
osskit --help
```

## Authentication

Unauthenticated GitHub API access is rate-limited. For normal use, set a token:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

The token only needs read access for public repository reports. For GitHub Actions, the default `${{ github.token }}` is enough for the included workflow when the workflow permissions are set to read issues, pull requests, actions, and contents.

## CLI usage

### Triage open issues

```bash
osskit triage owner/repo --output issue-triage.md
```

### Draft a changelog from recently merged PRs

```bash
osskit changelog owner/repo --days 30 --output changelog-draft.md
```

### Summarize recent CI failures

```bash
osskit ci-summary owner/repo --output ci-failures.md
```

To include log signals when permissions allow:

```bash
osskit ci-summary owner/repo --include-logs --output ci-failures.md
```

### Generate a combined weekly report

```bash
osskit weekly-report owner/repo --days 7 --output oss-triage-report.md
```

## GitHub Action usage

Create `.github/workflows/weekly-oss-report.yml` in your repository:

```yaml
name: Weekly OSS Triage Report

on:
  workflow_dispatch:
  schedule:
    - cron: "0 1 * * 1"

permissions:
  contents: read
  issues: read
  pull-requests: read
  actions: read

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate report
        uses: solcedar838/oss-triage-reporter@v0.1.0
        with:
          command: weekly-report
          output-file: oss-triage-report.md
      - name: Upload report artifact
        uses: actions/upload-artifact@v4
        with:
          name: oss-triage-report
          path: oss-triage-report.md
```

When testing this action inside the same repository, you can use:

```yaml
- uses: ./
  with:
    command: weekly-report
    output-file: oss-triage-report.md
```

## Example output

See [`examples/sample-report.md`](examples/sample-report.md).

A generated issue triage entry looks like this:

```md
- #42 Crash when opening config file
  - Priority: high
  - Suggested labels: bug, needs-repro
  - Maintainer note: Ask for reproduction steps, environment details, expected behavior, actual behavior, and logs.
```

## Project philosophy

This project starts with deterministic rules instead of AI-generated comments. That keeps the first version transparent, easy to test, and safe to run in public repositories.

Future optional integrations may add richer summaries, but the base tool should remain useful without requiring an API key or hosted service.

## Roadmap

- [ ] Add config file support for custom label mappings.
- [ ] Add markdown templates.
- [ ] Add optional issue comment creation mode.
- [ ] Add optional LLM provider interface for richer summaries.
- [ ] Publish to PyPI.
- [ ] Add marketplace-ready GitHub Action documentation.

## Development

Run tests:

```bash
python -m unittest discover -s tests
```

Install editable package:

```bash
python -m pip install -e .
```

## Maintainer program positioning

If you are using this project as evidence for an open-source maintainer support program, do not present it as widely adopted unless it is. A stronger honest positioning is:

> This is a small but real open-source maintainer tool. I am actively maintaining it, using it to generate issue triage and release-note drafts, and improving it based on practical repository maintenance workflows.

See [`docs/openai-oss-application-notes.md`](docs/openai-oss-application-notes.md) for a checklist of evidence to collect before applying.

## License

MIT
