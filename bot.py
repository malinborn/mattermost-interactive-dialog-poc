import asyncio
import json
import logging
import os

import httpx
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MATTERMOST_URL = os.getenv("MATTERMOST_URL", "http://localhost:8065")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
INTEGRATION_URL = os.getenv("INTEGRATION_URL", "http://localhost:8000")

GOOSE_ASCII = """```
  __
<(o )___
 ( ._> /
  `---'
```"""

SWAN_ASCII = """```
                           .
                          ":"
                        ___:____     |"\\/"|
                      ,'        `.    \\  /
                      |  O        \\___/  |
                    ~^~^~^~^~^~^~^~^~^~^~^~^~
```"""


class MattermostBot:
    def __init__(self, mattermost_url: str, token: str, integration_url: str):
        self.mattermost_url = mattermost_url.rstrip("/")
        self.token = token
        self.integration_url = integration_url
        self.ws_url = self._build_ws_url()
        self.bot_user_id: str | None = None
        self.http_client = httpx.AsyncClient(
            base_url=self.mattermost_url,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30.0,
        )

    def _build_ws_url(self) -> str:
        url = self.mattermost_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{url}/api/v4/websocket"

    async def get_me(self) -> dict:
        response = await self.http_client.get("/api/v4/users/me")
        response.raise_for_status()
        return response.json()

    async def post_message(self, channel_id: str, message: str) -> dict:
        response = await self.http_client.post(
            "/api/v4/posts",
            json={"channel_id": channel_id, "message": message},
        )
        response.raise_for_status()
        return response.json()

    async def post_message_with_buttons(self, channel_id: str) -> dict:
        payload = {
            "channel_id": channel_id,
            "message": "Выбери кто ты:",
            "props": {
                "attachments": [
                    {
                        "text": "",
                        "actions": [
                            {
                                "id": "goosebtn",
                                "name": "Гусь",
                                "type": "button",
                                "style": "primary",
                                "integration": {
                                    "url": f"{self.integration_url}/actions",
                                    "context": {"action": "goosebtn"},
                                },
                            },
                            {
                                "id": "danilovichbtn",
                                "name": "Лебедь",
                                "type": "button",
                                "style": "danger",
                                "integration": {
                                    "url": f"{self.integration_url}/actions",
                                    "context": {"action": "danilovichbtn"},
                                },
                            },
                        ],
                    }
                ]
            },
        }
        response = await self.http_client.post("/api/v4/posts", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_user(self, user_id: str) -> dict:
        response = await self.http_client.get(f"/api/v4/users/{user_id}")
        response.raise_for_status()
        return response.json()

    async def handle_posted_event(self, data: dict) -> None:
        post_data = json.loads(data.get("post", "{}"))
        user_id = post_data.get("user_id", "")
        channel_id = post_data.get("channel_id", "")
        message = post_data.get("message", "")

        if user_id == self.bot_user_id:
            return

        logger.info(f"Message from {user_id}: {message}")

        if "выбор" in message.lower():
            logger.info("Keyword 'выбор' detected, sending buttons")
            await self.post_message_with_buttons(channel_id)
        else:
            user = await self.get_user(user_id)
            username = user.get("username", "Unknown")
            response_message = f"{username} написал: {message}"
            await self.post_message(channel_id, response_message)

    async def run(self) -> None:
        me = await self.get_me()
        self.bot_user_id = me.get("id")
        logger.info(f"Bot started as user: {me.get('username')} (ID: {self.bot_user_id})")

        while True:
            try:
                await self._connect_websocket()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def _connect_websocket(self) -> None:
        logger.info(f"Connecting to WebSocket: {self.ws_url}")

        async with websockets.connect(self.ws_url) as ws:
            auth_challenge = json.dumps({
                "seq": 1,
                "action": "authentication_challenge",
                "data": {"token": self.token},
            })
            await ws.send(auth_challenge)
            logger.info("Sent authentication challenge")

            async for message in ws:
                try:
                    event = json.loads(message)
                    event_type = event.get("event")

                    if event_type == "hello":
                        logger.info("WebSocket connected and authenticated")
                    elif event_type == "posted":
                        await self.handle_posted_event(event.get("data", {}))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse message: {message}")
                except Exception as e:
                    logger.error(f"Error handling event: {e}")

    async def close(self) -> None:
        await self.http_client.aclose()


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required")
        return

    bot = MattermostBot(MATTERMOST_URL, BOT_TOKEN, INTEGRATION_URL)
    try:
        await bot.run()
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
