import asyncio
import concurrent.futures


class Loader:
    def load(self, url: str) -> str:
        raise NotImplementedError

    async def async_load(self, url: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, self.load, url)
            return result
