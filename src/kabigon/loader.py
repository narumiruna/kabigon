class Loader:
    def __call__(self, url: str) -> str:
        return self.load(url)

    def load(self, url: str) -> str:
        raise NotImplementedError


class LoaderError(Exception):
    pass
