"""
Fetch an investment analysis for HPQ (HP Inc.) from the local market server,
attaching thomas_context.txt as context and SEC_filings/2026-Q1-HPT.pdf as a document.
"""

import sys
from pathlib import Path
import requests

SERVER_URL = "http://localhost:9000"

RESOURCES = Path(__file__).parent.parent / "resources"
CONTEXT_FILE = RESOURCES / "thomas_context.txt"
# PDF_FILE = RESOURCES / "SEC_filings" / "2026-Q1-HPQ.pdf"
PDF_FILE = RESOURCES / "SEC_filings" / "hp1-excerpt.pdf"


def main():
    context = CONTEXT_FILE.read_text(encoding="utf-8")

    if not PDF_FILE.exists():
        print(f"ERROR: PDF not found at {PDF_FILE}", file=sys.stderr)
        sys.exit(1)

    with PDF_FILE.open("rb") as f:
        response = requests.post(
            f"{SERVER_URL}/market/analysis",
            data={"company": "HPQ", "context": context},
            files={"files": (PDF_FILE.name, f, "application/pdf")},
            timeout=120,
        )

    if not response.ok:
        print(f"ERROR {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    print(response.text)


if __name__ == "__main__":
    main()
