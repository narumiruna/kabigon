import asyncio


class Loader:
    def load_sync(self, url: str) -> str:
        return asyncio.run(self.async_load(url))

    async def async_load(self, url: str):
        return await asyncio.to_thread(self.load_sync, url)
