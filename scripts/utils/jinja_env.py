#!/usr/bin/env python3
"""
Jinja2 environment configuration and custom filters.
"""

from datetime import datetime
from typing import Any

import markdown as md  # type: ignore[import-untyped]
from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_jinja_env(template_dir: str = "templates") -> Environment:
    """Create configured Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Add custom filters
    env.filters["markdown"] = markdown_filter
    env.filters["date"] = date_filter
    env.filters["ordinal"] = ordinal_filter
    env.filters["percentage"] = percentage_filter
    env.filters["phone"] = phone_filter
    env.filters["titlecase"] = titlecase_filter
    env.filters["weekday"] = weekday_filter

    # Add global functions
    env.globals["now"] = datetime.now
    env.globals["today"] = datetime.today

    return env


def markdown_filter(text: str) -> str:
    """Convert markdown to HTML."""
    if not text:
        return ""

    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.toc",
        "markdown.extensions.nl2br",
        "markdown.extensions.sane_lists",
        "markdown.extensions.smarty",
    ]

    result = md.markdown(text, extensions=extensions)
    return str(result)


def date_filter(date_input: Any, format: str = "%B %d, %Y") -> str:
    """Format date for display."""
    if isinstance(date_input, str):
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            return date_input
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        return str(date_input)

    return date_obj.strftime(format)


def ordinal_filter(number: int) -> str:
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)."""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def percentage_filter(value: float, decimals: int = 0) -> str:
    """Format number as percentage."""
    if value < 1:
        value = value * 100

    if decimals == 0:
        return f"{int(value)}%"
    else:
        return f"{value:.{decimals}f}%"


def phone_filter(phone: str) -> str:
    """Format phone number."""
    # Remove non-digits
    digits = "".join(c for c in phone if c.isdigit())

    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone


def titlecase_filter(text: str) -> str:
    """Convert text to title case, handling exceptions."""
    if not text:
        return ""

    # Words that should remain lowercase
    lowercase_words = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "from",
        "in",
        "into",
        "nor",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }

    words = text.lower().split()
    result = []

    for i, word in enumerate(words):
        # Always capitalize first and last word
        if i == 0 or i == len(words) - 1:
            result.append(word.capitalize())
        elif word in lowercase_words:
            result.append(word)
        else:
            result.append(word.capitalize())

    return " ".join(result)


def weekday_filter(date_input: Any) -> str:
    """Get weekday name from date."""
    if isinstance(date_input, str):
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            return ""
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        return ""

    return date_obj.strftime("%A")


# Additional template helpers
class TemplateHelpers:
    """Additional template helper functions."""

    @staticmethod
    def format_course_code(code: str) -> str:
        """Format course code consistently."""
        # Ensure space between letters and numbers
        import re

        return re.sub(r"([A-Z]+)(\d+)", r"\1 \2", code)

    @staticmethod
    def format_credits(credits: int) -> str:
        """Format credit hours."""
        if credits == 1:
            return "1 credit"
        else:
            return f"{credits} credits"

    @staticmethod
    def format_crn(crn: str) -> str:
        """Format CRN for display."""
        return f"CRN: {crn}"

    @staticmethod
    def format_section(section: str) -> str:
        """Format section number."""
        if section.isdigit():
            return f"Section {section.zfill(3)}"
        return f"Section {section}"


def register_helpers(env: Environment) -> None:
    """Register helper functions with Jinja environment."""
    helpers = TemplateHelpers()

    env.globals["format_course_code"] = helpers.format_course_code
    env.globals["format_credits"] = helpers.format_credits
    env.globals["format_crn"] = helpers.format_crn
    env.globals["format_section"] = helpers.format_section
