# SmartGrade - Система тестирования

Система для создания и проведения тестов с защитой от списывания.

## Архитектура

- **Frontend**: HTML/CSS/JavaScript (статические файлы)
- **Backend**: Python + Flask
- **Database**: MongoDB (MongoEngine ODM)
- **AI**: Google Gemini API для генерации вопросов

## Установка и запуск

### 1. Установка зависимостей

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка базы данных

1. Создайте кластер MongoDB Atlas (бесплатно на https://mongodb.com)
2. Создайте пользователя базы данных
3. Скопируйте строку подключения
4. Отредактируйте файл `.env`:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/smartgrade?retryWrites=true&w=majority
PORT=3000
NODE_ENV=development
JWT_SECRET=ваш_секретный_ключ
TEACHER_PASSWORD=пароль_учителя
GEMINI_API_KEY=ваш_ключ_gemini
```

### 3. Запуск сервера

**Режим разработки:**
```bash
python app.py
```

**Режим продакшена (с gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:3000 app:app
```

### 4. Открытие в браузере

```
http://localhost:3000
```

## API Endpoints

### Авторизация
- `POST /api/login` - Вход учителя (возвращает JWT токен)
- `GET /api/verify-token` - Проверка токена

### Тесты
- `GET /api/tests` - Получить все тесты (требует авторизации)
- `GET /api/tests/:id` - Получить тест по ID для учителя (с ответами)
- `GET /api/tests/:id/student` - Получить тест для студента (без ответов)
- `POST /api/tests` - Создать новый тест
- `DELETE /api/tests/:id` - Удалить тест

### Результаты
- `GET /api/results` - Получить все результаты
- `GET /api/results/stats` - Получить статистику
- `POST /api/results` - Сохранить результат (серверное вычисление балла)

### Сессии
- `GET /api/sessions` - Получить активные сессии
- `POST /api/sessions` - Создать сессию
- `PUT /api/sessions/:id` - Обновить сессию (heartbeat)
- `DELETE /api/sessions/:id` - Удалить сессию

### AI
- `POST /api/generate-questions` - Генерация вопросов через Gemini API

## Структура проекта

```
smartgrade/
├── app.py              # Главный файл Flask сервера
├── config.py           # Конфигурация приложения
├── requirements.txt    # Python зависимости
├── .env               # Переменные окружения (НЕ КОММИТИТЬ!)
├── .gitignore         # Исключения Git
├── models_py/         # MongoEngine модели
│   ├── __init__.py   # Экспорт моделей
│   ├── test.py       # Модель теста
│   ├── result.py     # Модель результата
│   └── session.py    # Модель сессии
└── public/            # Статические файлы фронтенда
    ├── index.html         # Главная страница
    ├── teacher-dashboard.html  # Панель учителя
    ├── test-list.html     # Список тестов
    ├── test-player.html   # Плеер теста
    ├── results-dashboard.html  # Результаты
    └── ai-planner.html    # AI-генерация тестов
```

## Защита от списывания

### Anti-cheat механизмы:

1. **Серверная проверка ответов** - студент отправляет только свои ответы, сервер сам сверяет с правильными
2. **Правильные ответы скрыты** - API `/api/tests/:id/student` не возвращает правильные ответы
3. **Штраф за нарушения** - каждое предупреждение = -5% от балла (макс. 50%)
4. **Мониторинг сессий** - heartbeat отслеживает активность студента
5. **TTL сессий** - неактивные сессии автоматически удаляются через 10 минут

## Деплой

### Вариант 1: Heroku

```bash
# Создайте Procfile:
echo "web: gunicorn app:app" > Procfile

# Деплой
heroku create
heroku config:set MONGODB_URI=ваша_строка_подключения
heroku config:set JWT_SECRET=ваш_секрет
heroku config:set TEACHER_PASSWORD=пароль_учителя
heroku config:set GEMINI_API_KEY=ваш_ключ
git push heroku main
```

### Вариант 2: Render.com

1. Создайте аккаунт на Render.com
2. Подключите GitHub репозиторий
3. Добавьте переменные окружения (MONGODB_URI, JWT_SECRET, TEACHER_PASSWORD, GEMINI_API_KEY)
4. Укажите команду запуска: `gunicorn app:app`

### Вариант 3: VPS/Свой сервер

```bash
# Установите Python и MongoDB на сервер
# Клонируйте репозиторий
pip install -r requirements.txt

# Используйте systemd или supervisor для автозапуска
# Пример systemd сервиса:
# /etc/systemd/system/smartgrade.service
```

```ini
[Unit]
Description=SmartGrade Flask Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/smartgrade
ExecStart=/path/to/smartgrade/venv/bin/gunicorn -w 4 -b 0.0.0.0:3000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Безопасность

- Строка подключения к MongoDB хранится в `.env` файле
- `.env` добавлен в `.gitignore` и не попадёт в репозиторий
- JWT токены имеют срок действия 24 часа
- Правильные ответы не отправляются на фронтенд при получении списка тестов
- Пароль учителя хранится в переменной окружения

## Разработка

Для разработки включите `NODE_ENV=development` в `.env` файле для включения debug режима Flask.

```bash
python app.py
```

## Миграция с Node.js

Если вы мигрируете с Node.js версии:
1. Установите Python 3.9+
2. Установите зависимости: `pip install -r requirements.txt`
3. Используйте тот же `.env` файл
4. Данные MongoDB совместимы (те же коллекции и структура)
5. Фронтенд не требует изменений (те же API endpoints)
