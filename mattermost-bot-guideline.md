# Mattermost Bot Development Guideline

Руководство для ИИ-агентов по созданию Mattermost интеграций и ботов.

## Оглавление

1. [Типы интеграций](#типы-интеграций)
2. [Slash-команды с интерактивными кнопками](#slash-команды-с-интерактивными-кнопками)
3. [WebSocket бот](#websocket-бот)
4. [Критические требования](#критические-требования)
5. [Ссылки на документацию](#ссылки-на-документацию)

---

## Типы интеграций

Mattermost поддерживает несколько типов интеграций:

| Тип | Описание | Когда использовать |
|-----|----------|-------------------|
| **Slash Command** | Пользователь вызывает команду `/command` | Разовые действия по запросу |
| **Outgoing Webhook** | Триггер на определённые слова в сообщениях | Реакция на ключевые слова |
| **Incoming Webhook** | Отправка сообщений в канал извне | Уведомления от внешних систем |
| **Bot Account + WebSocket** | Полноценный бот с real-time подключением | Интерактивные боты, обработка всех сообщений |

---

## Slash-команды с интерактивными кнопками

### Архитектура

```
Пользователь вводит /command
        ↓
Mattermost → POST /slash (твой сервер)
        ↓
Сервер возвращает JSON с attachments и actions
        ↓
Пользователь видит сообщение с кнопками
        ↓
Пользователь нажимает кнопку
        ↓
Mattermost → POST /actions (integration.url из кнопки)
        ↓
Сервер возвращает {"update": {"message": "..."}}
```

### Формат ответа на slash-команду

```python
{
    "response_type": "in_channel",  # или "ephemeral" для сообщения только автору
    "attachments": [
        {
            "text": "Текст перед кнопками",
            "actions": [
                {
                    "id": "buttonid",           # ⚠️ ТОЛЬКО буквы и цифры!
                    "name": "Текст на кнопке",
                    "type": "button",
                    "style": "primary",         # primary, danger, default, good, warning, success
                    "integration": {
                        "url": "https://your-server.com/actions",
                        "context": {"action": "buttonid"}  # Любые данные для callback
                    }
                }
            ]
        }
    ]
}
```

### Формат ответа на нажатие кнопки

```python
{
    "update": {
        "message": "Новый текст сообщения",
        "props": {}  # Можно очистить кнопки
    },
    "ephemeral_text": "Опционально: приватное сообщение нажавшему"
}
```

### Payload от Mattermost при нажатии кнопки

```python
{
    "user_id": "abc123",
    "user_name": "username",
    "channel_id": "xyz789",
    "post_id": "postid123",
    "team_id": "teamid456",
    "context": {
        "action": "buttonid"  # То, что ты передал в integration.context
    }
}
```

---

## WebSocket бот

### Архитектура

```
Бот подключается к wss://mattermost-server/api/v4/websocket
        ↓
Отправляет authentication_challenge с токеном
        ↓
Получает события в реальном времени (posted, reaction_added, etc.)
        ↓
Отправляет сообщения через REST API POST /api/v4/posts
```

### Аутентификация WebSocket

```python
auth_message = {
    "seq": 1,
    "action": "authentication_challenge",
    "data": {"token": BOT_TOKEN}
}
await websocket.send(json.dumps(auth_message))
```

### Событие "posted" (новое сообщение)

```python
{
    "event": "posted",
    "data": {
        "post": "{\"id\":\"...\",\"message\":\"текст\",\"user_id\":\"...\",\"channel_id\":\"...\"}"
    }
}
```

⚠️ **Важно**: поле `post` приходит как JSON-строка, нужен двойной парсинг:
```python
post_data = json.loads(event["data"]["post"])
```

### Отправка сообщения с кнопками через API

```python
payload = {
    "channel_id": channel_id,
    "message": "Текст сообщения",
    "props": {
        "attachments": [
            {
                "text": "",
                "actions": [...]  # Тот же формат, что и для slash-команд
            }
        ]
    }
}
response = await http_client.post("/api/v4/posts", json=payload)
```

---

## Критические требования

### ⚠️ ID кнопок — только буквы и цифры

```python
# ❌ НЕПРАВИЛЬНО — кнопка не будет работать
"id": "my_button_1"

# ✅ ПРАВИЛЬНО
"id": "mybutton1"
```

**Источник**: [Interactive messages documentation](https://developers.mattermost.com/integrate/plugins/interactive-messages/) — "id in the actions array may only consist of letters and numbers, no other characters are allowed"

### ⚠️ python-multipart для form data

Slash-команды приходят как `application/x-www-form-urlencoded`, нужна библиотека:
```
python-multipart
```

Без неё FastAPI вернёт 500 ошибку при `await request.form()`.

### ⚠️ INTEGRATION_URL должен быть публичным

Кнопки содержат URL, на который Mattermost отправит POST при нажатии. Этот URL должен быть доступен с сервера Mattermost.

```python
# В .env
INTEGRATION_URL=https://your-public-domain.com
```

### ⚠️ Бот не должен отвечать сам себе

```python
if user_id == self.bot_user_id:
    return  # Игнорируем свои сообщения
```

### ⚠️ WebSocket реконнект

Соединение может разорваться. Всегда оборачивай в цикл с реконнектом:
```python
while True:
    try:
        await self._connect_websocket()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await asyncio.sleep(5)
```

### ⚠️ Whitelist для интеграций

Если Mattermost не отправляет запросы на твой сервер, проверь:
- **System Console** → **Environment** → **Developer** → **Allow untrusted internal connections to**
- Добавь домен твоего сервера в whitelist

---

## Зависимости Python

```
fastapi          # Web-фреймворк для HTTP эндпоинтов
uvicorn          # ASGI сервер
pydantic         # Валидация данных
python-multipart # Парсинг form data от slash-команд
websockets       # WebSocket клиент для бота
httpx            # Async HTTP клиент для Mattermost API
```

---

## Создание бота в Mattermost

1. **Integrations** → **Bot Accounts** → **Add Bot Account**
2. Укажи имя и описание
3. Скопируй **Access Token** — это `BOT_TOKEN`
4. Добавь бота в нужные каналы

---

## Docker структура

```
├── main.py           # FastAPI сервер (slash, actions)
├── bot.py            # WebSocket бот
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .env              # Секреты (не в git!)
```

### docker-compose.yml

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env

  bot:
    build: .
    command: ["python", "bot.py"]
    env_file:
      - .env
    depends_on:
      - app
```

---

## Ссылки на документацию

### Официальная документация

- **Interactive Messages (кнопки и меню)**: https://developers.mattermost.com/integrate/plugins/interactive-messages/
- **Interactive Dialogs (формы)**: https://developers.mattermost.com/integrate/plugins/interactive-dialogs/
- **Message Attachments**: https://docs.mattermost.com/developer/message-attachments.html
- **Bot Accounts**: https://developers.mattermost.com/integrate/reference/bot-accounts/
- **REST API**: https://api.mattermost.com/
- **WebSocket Events**: https://developers.mattermost.com/integrate/reference/websocket-events/

### Конфигурация сервера

- **Environment Configuration**: https://docs.mattermost.com/administration-guide/configure/environment-configuration-settings.html
- **Allow untrusted connections**: Раздел "Developer" в System Console

### Troubleshooting

- **Forum: Interactive Message Buttons**: https://forum.mattermost.com/t/solved-interactive-message-buttons/4669

---

## Чеклист перед деплоем

- [ ] ID кнопок содержат только буквы и цифры
- [ ] `INTEGRATION_URL` указывает на публичный URL
- [ ] `python-multipart` добавлен в requirements.txt
- [ ] Бот игнорирует свои собственные сообщения
- [ ] WebSocket имеет логику реконнекта
- [ ] `.env` добавлен в `.gitignore`
- [ ] Домен добавлен в whitelist Mattermost (если нужно)
