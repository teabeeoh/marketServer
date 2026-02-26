"""
Analysis Service Module

Provides financial analysis via the Anthropic Claude API.
"""

import os
import base64
import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


def build_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
    return anthropic.Anthropic(api_key=api_key)


def get_investment_analysis(
    company: str,
    context: str | None = None,
    files: list[tuple[str, bytes, str]] | None = None,
) -> str:
    """
    Generate an investment analysis for the given company using Claude.

    Args:
        company: Company identifier — name, ticker symbol, ISIN, or similar.
        context: Optional user-provided context describing the analyst's background
                 and expectations (appended to the system prompt).
        files: Optional list of (filename, content, media_type) tuples for
               additional documents (e.g. PDFs of annual reports, transcripts).

    Returns:
        Markdown-formatted investment analysis string.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set.
        anthropic.APIError: If the Anthropic API call fails.
    """
    client = build_client()
    print(f"Preparing analysis for company {company}")

    # Build system prompt
    system_parts = [
        "You are a professional financial analyst. Provide concise, structured investment analyses in Markdown format."
    ]
    if context:
        system_parts.append(context)
    system = "\n\n".join(system_parts)

    # Build message content
    content = []

    # Attach uploaded documents before the question so Claude reads them first
    if files:
        for filename, file_bytes, media_type in files:
            print(f"Attaching document: {filename} ({media_type}, {len(file_bytes)} bytes)")
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.b64encode(file_bytes).decode("utf-8"),
                },
                "title": filename,
            })

    content.append({
        "type": "text",
        "text": f"Can you give me an investment analysis for the following company: {company}?",
    })

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    print("Analysis done!")
    return "\n".join(
        block.text for block in message.content if block.type == "text"
    )
