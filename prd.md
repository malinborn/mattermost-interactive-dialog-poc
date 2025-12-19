# Prompt: Mattermost Interactive Integration (Goose & Danilovich)

Act as a Senior Python Developer. Create a FastAPI application that implements a Mattermost integration with interactive buttons.

### Core Logic:
1. **Slash Command Endpoint (`/slash`):**
   - Respond to a Mattermost POST request.
   - Return an interactive message with two buttons in the `attachments` section:
     - Button A: Text: "Гусь", ID: "goose_btn", Style: "primary".
     - Button B: Text: "Быдло", ID: "danilovich_btn", Style: "danger".
   - Ensure the `integration` URL in buttons points to the `/actions` endpoint.

2. **Action Handler Endpoint (`/actions`):**
   - Process the POST request from Mattermost when a button is clicked.
   - If `action` is "goose_btn", return an update that replaces the message with this ASCII art (wrapped in triple backticks for formatting):
     ```
      __
    <(o )___
     ( ._> /
      `---'
     ```
   - If `action` is "danilovich_btn", return an update that replaces the message with the string: "Данилович".

### Technical Requirements:
- **Framework:** FastAPI with Uvicorn.
- **Models:** Use Pydantic to define the structure of the incoming Mattermost payload (context, user_id, channel_id, etc.).
- **Response Format:** Return a JSON compatible with Mattermost's "Integration Actions" (use `update` field to replace the original message).
- **Environment:** Add a `requirements.txt` with `fastapi`, `uvicorn`, and `pydantic`.
- **Logging:** Add print/logging statements to see the raw JSON received from Mattermost for debugging.

### Deliverables:
1. `main.py` with the complete server logic.
2. `requirements.txt`.
3. A short README on how to set the "Request URL" and "Integration URL" in Mattermost.

### Deploy 
Also please make me an instructions on how to deploy this application to a server.
I prefer docker container, secrets in .env file, i will store the code in public github so please do not store any secrets in repo