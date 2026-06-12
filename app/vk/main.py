import asyncio
import logging
from typing import Any

from app.config import get_settings
from app.db.session import init_db
from app.vk.client import VkApiError, VkClient
from app.vk.handlers import VkBotHandler
from app.vk.scheduler import run_scheduler

logger = logging.getLogger(__name__)


async def run_long_poll(client: VkClient, handler: VkBotHandler) -> None:
    server_data = await client.get_long_poll_server()
    server = server_data["server"]
    key = server_data["key"]
    ts = server_data["ts"]

    while True:
        try:
            data = await client.long_poll_check(server=server, key=key, ts=ts)
        except Exception:
            logger.exception("VK Long Poll request failed")
            await asyncio.sleep(3)
            continue

        failed = data.get("failed")
        if failed == 1:
            ts = data["ts"]
            continue
        if failed in {2, 3}:
            logger.warning("VK Long Poll key expired, requesting new server")
            server_data = await client.get_long_poll_server()
            server = server_data["server"]
            key = server_data["key"]
            ts = server_data["ts"]
            continue

        ts = data.get("ts", ts)
        for update in data.get("updates", []):
            await handle_update(handler, update)


async def handle_update(handler: VkBotHandler, update: dict[str, Any]) -> None:
    if update.get("type") != "message_new":
        return

    message = update.get("object", {}).get("message", {})
    if not message:
        return

    from_id = message.get("from_id")
    if not isinstance(from_id, int) or from_id < 0:
        return

    try:
        await handler.handle_message(message)
    except VkApiError as exc:
        logger.warning("VK API error while handling message: %s", exc)
    except Exception:
        logger.exception("Failed to handle VK message")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    if settings.vk_group_id is None or not settings.vk_group_token:
        raise RuntimeError("VK_GROUP_ID and VK_GROUP_TOKEN are required for VK bot")

    if settings.auto_create_db:
        await init_db()

    client = VkClient(
        group_id=settings.vk_group_id,
        token=settings.vk_group_token,
        api_version=settings.vk_api_version,
    )
    handler = VkBotHandler(client)
    scheduler_task = asyncio.create_task(run_scheduler(client))

    try:
        await run_long_poll(client, handler)
    finally:
        scheduler_task.cancel()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
