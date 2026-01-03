import kabigon


def main() -> None:
    url = "https://x.com/BillGertz/status/2005141727489708352"

    # Use TwitterLoader directly or Compose with fallback
    loader = kabigon.Compose(
        [
            kabigon.TwitterLoader(),
            kabigon.PlaywrightLoader(),  # Fallback
        ]
    )

    result = loader.load_sync(url)
    print(result)


if __name__ == "__main__":
    main()
