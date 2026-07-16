"""
Sample data for email previews.

Loads the canned sample digest shipped with the package, used for
email previews and test sends.
"""

from importlib import resources


def load_sample_digest() -> str:
    """Return the canned sample digest markdown shipped with the package."""
    sample_file = resources.files("mlb_digest").joinpath("sample_digest.md")
    return sample_file.read_text(encoding="utf-8")
