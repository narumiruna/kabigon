import kabigon


def main() -> None:
    url = "https://x.com/BillGertz/status/2005141727489708352"

    result = kabigon.load_url_sync(url)
    print(result)


if __name__ == "__main__":
    main()
