"""Regenerate vectors/eyecite-<version>/ from that eyecite release's test suite.

Usage: uv run tools/export_eyecite.py 2.7.8
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    version = sys.argv[1]
    checkout = ROOT / ".cache" / f"eyecite-{version}"
    if not checkout.exists():
        subprocess.run(
            [
                "git",
                "clone",
                "-q",
                "--depth",
                "1",
                "--branch",
                f"v{version}",
                "https://github.com/freelawproject/eyecite.git",
                str(checkout),
            ],
            check=True,
        )
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(["uv", "sync", "-q", "--project", str(checkout)], check=True)

    dest = ROOT / "vectors" / f"eyecite-{version}"
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "uv",
            "run",
            "-q",
            "--project",
            str(checkout),
            "python",
            str(ROOT / "tools" / "_capture_find.py"),
            str(checkout),
            version,
            str(dest / "find.jsonl"),
        ],
        check=True,
    )
    (dest / "SOURCE.json").write_text(
        json.dumps(
            {
                "engine": "eyecite",
                "version": version,
                "commit": commit,
                "repository": "https://github.com/freelawproject/eyecite",
                "license": "BSD-2-Clause",
                "exporter": "tools/export_eyecite.py",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
