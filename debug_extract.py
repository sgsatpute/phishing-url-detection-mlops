"""
One-off diagnostic: run extract_features() on a single URL and print every
feature value, so we can see exactly what the model is being fed — and
which features silently fell back to a default because the page didn't
load, WHOIS failed, etc.

Usage:
    python debug_extract.py http://paypal-secure-verify.tk
"""

import sys

from network_security.utils.ml_utils.feature_extraction import (
    _fetch_page,
    extract_features,
)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python debug_extract.py <url>")
        return

    url = sys.argv[1]

    # Check page fetch status directly first, since most of the "live"
    # features (Favicon, Request_URL, SFH, Google_Index, URL_of_Anchor,
    # Links_in_tags) all collapse together if this fails.
    response = _fetch_page(url if url.startswith(("http://", "https://")) else "http://" + url)
    if response is None:
        print(f"Page fetch FAILED for {url} — this is why several features default together.\n")
    else:
        print(f"Page fetch succeeded: status {response.status_code}, {len(response.text)} bytes of HTML\n")

    df = extract_features(url)
    for col in df.columns:
        print(f"{col:<32} {df[col].iloc[0]}")


if __name__ == "__main__":
    main()