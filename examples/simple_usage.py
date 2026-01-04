"""Simple usage example of kabigon.load_url()"""

import kabigon


def main() -> None:
    # Simple one-liner - automatically uses the best loader for the URL
    url = "https://www.google.com"
    text = kabigon.load_url_sync(url)

    print(f"Loaded {len(text)} characters from {url}")
    print("\nContent preview:")
    print(text[:500])


if __name__ == "__main__":
    main()
