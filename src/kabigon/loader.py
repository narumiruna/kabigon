import asyncio


class Loader:
    def load_sync(self, url: str) -> str:
        return asyncio.run(self.load(url))

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
