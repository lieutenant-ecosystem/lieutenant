from typing import Dict, Any, List

import aiohttp


async def get_raw_http_data(url: str, header: Dict[str, Any]) -> Dict[str, Any] | List[Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=header) as response:
            response.raise_for_status()
            return await response.json()
