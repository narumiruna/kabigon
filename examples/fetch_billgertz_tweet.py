from kabigon import loaders


def main() -> None:
    url = "https://x.com/BillGertz/status/2005141727489708352"

    # Use TwitterLoader directly or Compose with fallback
    loader = loaders.Compose(
        [
            loaders.TwitterLoader(),
            loaders.PlaywrightLoader(),  # Fallback
        ]
    )

    result = loader.load_sync(url)
    print(result)


if __name__ == "__main__":
    main()
