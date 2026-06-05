from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence

BUG_WORDS = {
    "bug", "broken", "crash", "crashes", "error", "failed", "failure", "fail", "exception",
    "traceback", "wrong", "regression", "panic", "timeout", "security", "vulnerability",
}
FEATURE_WORDS = {"feature", "request", "support", "add", "allow", "enhancement", "proposal"}
DOC_WORDS = {"doc", "docs", "documentation", "readme", "typo", "example", "guide"}
QUESTION_WORDS = {"how", "question", "help", "clarify", "usage", "install", "setup"}
HIGH_PRIORITY_WORDS = {"security", "vulnerability", "data loss", "crash", "regression", "broken", "production"}
LOW_INFO_WORDS = {"reproduce", "steps", "version", "expected", "actual", "logs", "environment"}


def _label_names(item: Mapping[str, Any]) -> List[str]:
    return [str(label.get("name", "")).lower() for label in item.get("labels", []) if isinstance(label, Mapping)]


def _text(item: Mapping[str, Any]) -> str:
    return f"{item.get('title', '')}\n{item.get('body') or ''}\n{' '.join(_label_names(item))}".lower()


def classify_issue(issue: Mapping[str, Any]) -> Dict[str, str]:
    text = _text(issue)
    labels = set(_label_names(issue))

    if labels & {"bug", "type: bug"} or any(word in text for word in BUG_WORDS):
        category = "bug"
    elif labels & {"enhancement", "feature", "feature request"} or any(word in text for word in FEATURE_WORDS):
        category = "feature"
    elif labels & {"documentation", "docs"} or any(word in text for word in DOC_WORDS):
        category = "docs"
    elif any(word in text for word in QUESTION_WORDS):
        category = "question"
    else:
        category = "needs-triage"

    if any(word in text for word in HIGH_PRIORITY_WORDS):
        priority = "high"
    elif category in {"bug", "needs-triage"}:
        priority = "medium"
    else:
        priority = "low"

    body = (issue.get("body") or "").lower()
    has_basic_debug_info = sum(1 for word in LOW_INFO_WORDS if word in body) >= 2
    needs_info = "yes" if category == "bug" and not has_basic_debug_info else "no"

    suggested_labels = {
        "bug": "bug",
        "feature": "enhancement",
        "docs": "documentation",
        "question": "question",
        "needs-triage": "needs-triage",
    }[category]
    if needs_info == "yes":
        suggested_labels += ", needs-repro"

    return {
        "category": category,
        "priority": priority,
        "needs_info": needs_info,
        "suggested_labels": suggested_labels,
    }


def issue_reply_hint(issue: Mapping[str, Any], classification: Mapping[str, str]) -> str:
    category = classification["category"]
    if classification.get("needs_info") == "yes":
        return "Ask for reproduction steps, environment details, expected behavior, actual behavior, and logs."
    if category == "feature":
        return "Ask for the use case, expected API/UX, and whether they can help test a preview."
    if category == "docs":
        return "Confirm the affected docs page and invite a small PR if the fix is straightforward."
    if category == "question":
        return "Answer briefly, then point to the relevant docs or example if available."
    return "Review manually and decide whether to label, close, or request more context."


def make_issue_triage_report(repo_slug: str, issues: Sequence[Mapping[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Issue Triage Report for `{repo_slug}`",
        "",
        f"Generated: {now}",
        "",
        f"Open issues reviewed: **{len(issues)}**",
        "",
    ]
    if not issues:
        lines.append("No open issues were found.")
        return "\n".join(lines).rstrip() + "\n"

    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    classified: Dict[int, Dict[str, str]] = {}
    for issue in issues:
        c = classify_issue(issue)
        classified[int(issue.get("number", 0))] = c
        grouped[c["category"]].append(issue)

    order = ["bug", "feature", "docs", "question", "needs-triage"]
    for category in order:
        items = grouped.get(category, [])
        if not items:
            continue
        lines.extend([f"## {category.title().replace('-', ' ')}", ""])
        for issue in items:
            number = issue.get("number", "?")
            title = issue.get("title", "Untitled")
            url = issue.get("html_url", "")
            c = classified[int(issue.get("number", 0))]
            lines.append(f"- #{number} [{title}]({url})")
            lines.append(f"  - Priority: **{c['priority']}**")
            lines.append(f"  - Suggested labels: `{c['suggested_labels']}`")
            lines.append(f"  - Maintainer note: {issue_reply_hint(issue, c)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def classify_changelog_item(pr: Mapping[str, Any]) -> str:
    text = _text(pr)
    labels = set(_label_names(pr))
    if labels & {"bug", "fix"} or re.search(r"\b(fix|fixed|bug|regression|crash)\b", text):
        return "Fixed"
    if labels & {"documentation", "docs"} or any(word in text for word in DOC_WORDS):
        return "Documentation"
    if labels & {"breaking-change", "breaking"} or "breaking" in text:
        return "Changed"
    if labels & {"enhancement", "feature"} or re.search(r"\b(add|added|support|feature|new)\b", text):
        return "Added"
    return "Changed"


def make_changelog_report(repo_slug: str, prs: Sequence[Mapping[str, Any]], days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Changelog Draft for `{repo_slug}`",
        "",
        f"Generated: {now}",
        f"Window: last {days} days, based on merged pull requests.",
        "",
    ]
    if not prs:
        lines.append("No recently merged pull requests were found for this window.")
        return "\n".join(lines).rstrip() + "\n"

    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for pr in prs:
        grouped[classify_changelog_item(pr)].append(pr)

    for section in ["Added", "Changed", "Fixed", "Documentation"]:
        items = grouped.get(section, [])
        if not items:
            continue
        lines.extend([f"## {section}", ""])
        for pr in items:
            title = clean_title(str(pr.get("title", "Untitled")))
            number = pr.get("number", "?")
            url = pr.get("html_url", "")
            author = (pr.get("user") or {}).get("login", "unknown")
            lines.append(f"- {title} ([#{number}]({url}) by @{author})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def clean_title(title: str) -> str:
    title = re.sub(r"^(feat|fix|docs|chore|refactor|test|ci)(\(.+?\))?:\s*", "", title, flags=re.I)
    return title[:1].upper() + title[1:] if title else title


def summarize_log(log_text: str, max_lines: int = 12) -> List[str]:
    patterns = [
        r"error", r"failed", r"failure", r"traceback", r"exception", r"module not found",
        r"npm err", r"exit code", r"assertionerror", r"syntaxerror", r"typeerror",
    ]
    selected: List[str] = []
    seen = set()
    for line in log_text.splitlines():
        cleaned = strip_ansi(line).strip()
        if not cleaned or len(cleaned) > 500:
            continue
        low = cleaned.lower()
        if any(re.search(pattern, low) for pattern in patterns):
            if cleaned not in seen:
                selected.append(cleaned)
                seen.add(cleaned)
        if len(selected) >= max_lines:
            break
    return selected


def strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def make_ci_report(repo_slug: str, runs: Sequence[Mapping[str, Any]], log_summaries: Mapping[int, Sequence[str]] | None = None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    log_summaries = log_summaries or {}
    lines = [
        f"# CI Failure Summary for `{repo_slug}`",
        "",
        f"Generated: {now}",
        "",
        f"Failed workflow runs reviewed: **{len(runs)}**",
        "",
    ]
    if not runs:
        lines.append("No recent failed workflow runs were found.")
        return "\n".join(lines).rstrip() + "\n"

    for run in runs:
        run_id = int(run.get("id", 0))
        name = run.get("name") or run.get("display_title") or "Unnamed workflow"
        url = run.get("html_url", "")
        branch = run.get("head_branch", "unknown")
        event = run.get("event", "unknown")
        conclusion = run.get("conclusion", "failure")
        created = run.get("created_at", "unknown time")
        lines.append(f"## [{name}]({url})")
        lines.append("")
        lines.append(f"- Run ID: `{run_id}`")
        lines.append(f"- Branch: `{branch}`")
        lines.append(f"- Event: `{event}`")
        lines.append(f"- Conclusion: `{conclusion}`")
        lines.append(f"- Created: `{created}`")
        hints = list(log_summaries.get(run_id, []))
        if hints:
            lines.append("- Log signals:")
            for hint in hints:
                lines.append(f"  - `{hint}`")
        else:
            lines.append("- Log signals: not collected. Re-run with `--include-logs` if permissions allow.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def make_weekly_report(repo_slug: str, issues: Sequence[Mapping[str, Any]], prs: Sequence[Mapping[str, Any]], runs: Sequence[Mapping[str, Any]], days: int) -> str:
    parts = [
        f"# Weekly OSS Maintainer Report for `{repo_slug}`\n",
        make_issue_triage_report(repo_slug, issues),
        make_changelog_report(repo_slug, prs, days),
        make_ci_report(repo_slug, runs),
    ]
    return "\n---\n\n".join(part.strip() for part in parts if part.strip()) + "\n"
