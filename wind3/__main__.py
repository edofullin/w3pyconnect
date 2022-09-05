import asyncio
import sys

from . import W3API

async def main():
    api = W3API(sys.argv[1], sys.argv[2])

    await api.login()
    counters = await api.get_lines_counters()

    print(counters)

    await api.close()

asyncio.run(main())