"""Simple usage example of kabigon.load_url()"""

import kabigon

# Simple one-liner - automatically uses the best loader for the URL
url = "https://www.google.com"
text = kabigon.load_url_sync(url)

print(f"Loaded {len(text)} characters from {url}")
print("\nContent preview:")
print(text[:500])
