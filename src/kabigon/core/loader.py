import asyncio
from abc import ABC
from abc import abstractmethod


class Loader(ABC):
    def load_sync(self, url: str) -> str:
        return asyncio.run(self.load(url))

    @abstractmethod
    async def load(self, url: str) -> str:
        raise NotImplementedError
