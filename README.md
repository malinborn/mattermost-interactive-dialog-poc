# Mattermost Goose & Danilovich Integration

FastAPI-приложение для Mattermost с интерактивными кнопками.

## Функционал

- **Slash-команда** — отправляет сообщение с двумя кнопками: "Гусь" и "Быдло"
- **Обработчик действий** — заменяет сообщение на ASCII-арт гуся или текст "Данилович"

## Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python main.py
```

Сервер будет доступен на `http://localhost:8000`

## Docker деплой

### 1. Подготовка

```bash
# Скопируйте .env.example в .env
cp .env.example .env

# Отредактируйте .env — укажите публичный URL вашего сервера
# INTEGRATION_URL=https://your-domain.com
```

### 2. Сборка и запуск

```bash
docker compose up -d --build
```

### 3. Проверка

```bash
curl http://localhost:8000/health
```

## Настройка Mattermost

### 1. Создание Slash-команды

1. Откройте **Main Menu** → **Integrations** → **Slash Commands**
2. Нажмите **Add Slash Command**
3. Заполните:
   - **Title**: Goose
   - **Command Trigger Word**: `goose` (или любое другое)
   - **Request URL**: `https://your-domain.com/slash`
   - **Request Method**: POST
4. Сохраните команду

### 2. Разрешение исходящих вебхуков

Убедитесь, что в **System Console** → **Integrations** → **Integration Management**:
- **Enable integrations to override usernames**: включено
- **Enable integrations to override profile picture icons**: включено
- **Enable incoming webhooks**: включено
- **Enable outgoing webhooks**: включено
- **Enable slash commands**: включено

### 3. Белый список URL

В **System Console** → **Environment** → **Developer** добавьте ваш домен в **Allow untrusted internal connections to** (если сервер в локальной сети).

## Деплой на сервер

### Вариант 1: Docker на VPS

```bash
# На сервере
git clone https://github.com/your-repo/mattermost-interactive-dialog-test.git
cd mattermost-interactive-dialog-test

# Создайте .env с вашим публичным URL
echo "INTEGRATION_URL=https://your-domain.com" > .env

# Запустите
docker compose up -d --build
```

### Вариант 2: С reverse proxy (nginx)

Пример конфигурации nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Вариант 3: Docker Compose с Traefik

```yaml
services:
  app:
    build: .
    env_file:
      - .env
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.goose.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.goose.entrypoints=websecure"
      - "traefik.http.routers.goose.tls.certresolver=letsencrypt"
```

## API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/slash` | POST | Обработка slash-команды |
| `/actions` | POST | Обработка нажатия кнопок |
| `/health` | GET | Health check |

## Использование

1. В Mattermost введите `/goose` (или вашу команду)
2. Появится сообщение с двумя кнопками
3. Нажмите на кнопку — сообщение заменится на результат
# mattermost-interactive-dialog-poc
