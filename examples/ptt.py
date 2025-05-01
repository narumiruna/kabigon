from kabigon.ptt import PttLoader


def main() -> None:
    url = "https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html"
    result = PttLoader().load(url)
    print(result)


if __name__ == "__main__":
    main()
