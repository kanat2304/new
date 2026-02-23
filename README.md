# SmartGrade - Система тестирования

Система для создания и проведения тестов с защитой от списывания.

## Архитектура

- **Frontend**: HTML/CSS/JavaScript (статические файлы)
- **Backend**: Node.js + Express
- **Database**: MongoDB

## Установка и запуск

### 1. Установка зависимостей

```bash
npm install
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
```

### 3. Запуск сервера

**Режим разработки (с автоперезагрузкой):**
```bash
npm run dev
```

**Режим продакшена:**
```bash
npm start
```

### 4. Открытие в браузере

```
http://localhost:3000
```

## API Endpoints

### Тесты
- `GET /api/tests` - Получить все тесты
- `GET /api/tests/:id` - Получить тест по ID
- `POST /api/tests` - Создать новый тест
- `DELETE /api/tests/:id` - Удалить тест

### Результаты
- `GET /api/results` - Получить все результаты
- `GET /api/results/stats` - Получить статистику
- `POST /api/results` - Сохранить результат

### Сессии
- `GET /api/sessions` - Получить активные сессии
- `POST /api/sessions` - Создать сессию
- `PUT /api/sessions/:id` - Обновить сессию
- `DELETE /api/sessions/:id` - Удалить сессию

## Структура проекта

```
smartgrade/
├── server.js           # Главный файл сервера
├── package.json        # Зависимости Node.js
├── .env               # Переменные окружения (НЕ КОММИТИТЬ!)
├── .gitignore         # Исключения Git
├── api-config.js      # Конфигурация API для фронтенда
├── models/            # Mongoose схемы
│   ├── Test.js       # Схема теста
│   ├── Result.js     # Схема результата
│   └── Session.js    # Схема сессии
├── index.html         # Главная страница
├── teacher-dashboard.html  # Панель учителя
├── test-list.html     # Список тестов
├── test-player.html   # Плеер теста
└── results-dashboard.html  # Результаты
```

## Деплой

### Вариант 1: Heroku (бесплатно)

1. Создайте аккаунт на Heroku
2. Установите Heroku CLI
3. Выполните:
```bash
heroku create
heroku config:set MONGODB_URI=ваша_строка_подключения
git push heroku main
```

### Вариант 2: Render.com (бесплатно)

1. Создайте аккаунт на Render.com
2. Подключите GitHub репозиторий
3. Добавьте переменную окружения MONGODB_URI

### Вариант 3: VPS/Свой сервер

1. Установите Node.js и MongoDB на сервер
2. Клонируйте репозиторий
3. Настройте .env файл
4. Используйте PM2 для автозапуска:
```bash
npm install -g pm2
pm2 start server.js
```

## Безопасность

- Строка подключения к MongoDB хранится в `.env` файле
- `.env` добавлен в `.gitignore` и не попадёт в репозиторий
- Правильные ответы не отправляются на фронтенд при получении списка тестов

## Разработка

Для разработки используется nodemon для автоматической перезагрузки сервера при изменении файлов.

```bash
npm run dev
```
