from kabigon.loaders.twitter import TwitterLoader


def main() -> None:
    url = "https://x.com/howie_serious/status/1917768568135115147"
    result = TwitterLoader().load_sync(url)
    print(result)


if __name__ == "__main__":
    main()
