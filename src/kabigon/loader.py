class Loader:
    def load(self, url: str) -> str:
        raise NotImplementedError


class LoaderError(Exception):
    pass
