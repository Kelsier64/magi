#!/usr/bin/env python3

import urllib.request
import re

def main():
    url = "http://example.com"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return

    match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if match:
        print(match.group(1).strip())
    else:
        print("No <title> tag found.")

if __name__ == "__main__":
    main()
