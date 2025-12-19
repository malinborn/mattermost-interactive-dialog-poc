import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mattermost Goose & Danilovich Integration")

INTEGRATION_URL = os.getenv("INTEGRATION_URL", "http://localhost:8000")
MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN", "")

logger.info(f"Starting with INTEGRATION_URL: {INTEGRATION_URL}")


class MattermostContext(BaseModel):
    action: str | None = None


class MattermostActionPayload(BaseModel):
    user_id: str | None = None
    user_name: str | None = None
    channel_id: str | None = None
    channel_name: str | None = None
    team_id: str | None = None
    team_domain: str | None = None
    post_id: str | None = None
    trigger_id: str | None = None
    context: MattermostContext | None = None


GOOSE_ASCII = """```
  __
<(o )___
 ( ._> /
  `---'
```"""


@app.post("/slash")
async def slash_command(request: Request) -> dict[str, Any]:
    """Handle slash command and return interactive message with buttons."""
    form_data = await request.form()
    payload = dict(form_data)
    logger.info(f"Received slash command payload: {payload}")

    if MATTERMOST_TOKEN and payload.get("token") != MATTERMOST_TOKEN:
        logger.warning(f"Invalid token received: {payload.get('token')}")
        raise HTTPException(status_code=401, detail="Invalid token")

    response = {
        "response_type": "in_channel",
        "attachments": [
            {
                "text": "Выбери кто ты:",
                "actions": [
                    {
                        "id": "goosebtn",
                        "name": "Гусь",
                        "type": "button",
                        "style": "primary",
                        "integration": {
                            "url": f"{INTEGRATION_URL}/actions",
                            "context": {"action": "goosebtn"},
                        },
                    },
                    {
                        "id": "danilovichbtn",
                        "name": "Лебедь",
                        "type": "button",
                        "style": "danger",
                        "integration": {
                            "url": f"{INTEGRATION_URL}/actions",
                            "context": {"action": "danilovichbtn"},
                        },
                    },
                ],
            }
        ],
    }
    logger.info(f"Sending slash response: {response}")
    return response


@app.post("/actions")
async def action_handler(request: Request) -> dict[str, Any]:
    """Handle button click actions from Mattermost."""
    payload_json = await request.json()
    logger.info(f"Received action payload: {payload_json}")

    payload = MattermostActionPayload(**payload_json)
    action = payload.context.action if payload.context else None

    if action == "goosebtn":
        response = {"update": {"message": GOOSE_ASCII}}
    elif action == "danilovichbtn":
        response = {"update": {"message": "Данилович"}}
    else:
        response = {"update": {"message": "Неизвестное действие"}}

    logger.info(f"Sending action response: {response}")
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
