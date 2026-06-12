import json
import secrets
from typing import Any

import aiohttp


class VkApiError(Exception):
    pass


class VkClient:
    def __init__(self, *, group_id: int, token: str, api_version: str) -> None:
        self.group_id = group_id
        self.token = token
        self.api_version = api_version
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    async def method(self, name: str, **params: Any) -> dict[str, Any]:
        payload = {
            **params,
            "access_token": self.token,
            "v": self.api_version,
        }
        async with self.session.post(f"https://api.vk.com/method/{name}", data=payload) as response:
            data = await response.json()

        if "error" in data:
            error = data["error"]
            raise VkApiError(f"{error.get('error_code')}: {error.get('error_msg')}")

        return data["response"]

    async def get_long_poll_server(self) -> dict[str, Any]:
        return await self.method("groups.getLongPollServer", group_id=self.group_id)

    async def users_get(self, user_id: int) -> dict[str, Any] | None:
        response = await self.method("users.get", user_ids=user_id)
        if not response:
            return None
        return response[0]

    async def send_message(
        self,
        *,
        peer_id: int,
        message: str,
        keyboard: dict[str, Any] | None = None,
    ) -> None:
        params: dict[str, Any] = {
            "peer_id": peer_id,
            "message": message,
            "random_id": secrets.randbelow(2_147_483_647),
        }
        if keyboard is not None:
            params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)

        await self.method("messages.send", **params)

    async def long_poll_check(self, *, server: str, key: str, ts: str, wait: int = 25) -> dict[str, Any]:
        params = {
            "act": "a_check",
            "key": key,
            "ts": ts,
            "wait": wait,
        }
        async with self.session.get(server, params=params, timeout=wait + 10) as response:
            return await response.json()
