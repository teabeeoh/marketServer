"""
Analysis Service Module

Provides financial analysis via the Anthropic Claude API.
"""

import os
import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2048


def build_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
    return anthropic.Anthropic(api_key=api_key)


def get_investment_analysis(company: str) -> str:
    """
    Generate an investment analysis for the given company using Claude.

    Args:
        company: Company identifier — name, ticker symbol, ISIN, or similar.

    Returns:
        Markdown-formatted investment analysis string.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set.
        anthropic.APIError: If the Anthropic API call fails.
    """
    client = build_client()
    print(f"Preparing anylsis for company {company}")
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        system="You are a professional financial analyst. Provide concise, structured investment analyses in Markdown format.",
        messages=[
            {
                "role": "user",
                "content": f"Can you give me an investment analysis for the following company: {company}?",
            }
        ],
    )
    print(f"Analyis done!")
    return "\n".join(
        block.text for block in message.content if block.type == "text"
    )
