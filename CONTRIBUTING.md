# Contributing

Thanks for your interest in improving OSS Triage Reporter.

## Good first contributions

- Improve issue classification rules.
- Add more tests for changelog categories.
- Improve GitHub Action examples.
- Add sample reports from real public repositories.
- Improve documentation and troubleshooting notes.

## Development setup

```bash
git clone https://github.com/solcedar838/oss-triage-reporter.git
cd oss-triage-reporter
python -m pip install -e .
python -m unittest discover -s tests
```

## Pull request checklist

- Keep the tool lightweight.
- Add or update tests for behavior changes.
- Keep generated output readable as plain Markdown.
- Avoid requiring hosted services for core features.
