from kabigon.loaders.truthsocial import TruthSocialLoader


def main() -> None:
    url = "https://truthsocial.com/@realDonaldTrump/posts/115830428767897167"

    # Use TruthSocialLoader directly
    loader = TruthSocialLoader()
    result = loader.load_sync(url)
    print(result)


if __name__ == "__main__":
    main()
