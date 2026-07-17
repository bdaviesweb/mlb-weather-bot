import os
import subprocess
import tempfile

import requests


def post_to_slack(webhook_url, message, webhook_name):
    if not webhook_url:
        print(f"⚠️  {webhook_name} is not configured - skipping Slack post")
        return False

    response = requests.post(
        webhook_url,
        json=message,
        headers={'Content-Type': 'application/json'},
        timeout=10,
    )
    if response.status_code != 200:
        raise ValueError(f"Slack request failed: {response.status_code}, {response.text}")
    return True


def slack_blocks_to_markdown(message):
    lines = [f"## {message.get('text', 'Weather alert')}"]

    for block in message.get("blocks", []):
        block_type = block.get("type")
        if block_type == "header":
            text = block.get("text", {}).get("text", "")
            if text:
                lines.extend(["", f"### {text}"])
        elif block_type == "section":
            text = block.get("text", {}).get("text")
            if text:
                lines.extend(["", text])
            for field in block.get("fields", []):
                field_text = field.get("text", "")
                if field_text:
                    lines.extend(["", field_text])
        elif block_type == "context":
            context = " ".join(
                element.get("text", "")
                for element in block.get("elements", [])
                if element.get("text")
            )
            if context:
                lines.extend(["", f"_{context}_"])

    return "\n".join(lines).replace("<!channel> ", "")


def post_to_github_issue(title, message, labels=None):
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("⚠️  GITHUB_REPOSITORY or GITHUB_TOKEN is not configured - skipping GitHub issue")
        return False

    body = slack_blocks_to_markdown(message)
    label_args = []
    for label in labels or []:
        label_args.extend(["--label", label])

    existing = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--search",
            f"{title} in:title",
            "--json",
            "number",
            "--jq",
            ".[0].number // empty",
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": token},
    )

    issue_number = existing.stdout.strip()
    with tempfile.NamedTemporaryFile("w", delete=False) as body_file:
        body_file.write(body)
        body_path = body_file.name

    if issue_number:
        command = [
            "gh",
            "issue",
            "comment",
            issue_number,
            "--repo",
            repo,
            "--body-file",
            body_path,
        ]
    else:
        command = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body-file",
            body_path,
            *label_args,
        ]

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": token},
    )
    if result.returncode != 0:
        print(f"❌ GitHub issue notification failed: {result.stderr.strip()}")
        return False

    print("✅ GitHub issue notification recorded")
    return True


def notify(title, message, webhook_url=None, webhook_name="SLACK_WEBHOOK_URL", labels=None):
    if post_to_slack(webhook_url, message, webhook_name):
        return "slack"
    if post_to_github_issue(title, message, labels=labels):
        return "github_issue"
    return None
