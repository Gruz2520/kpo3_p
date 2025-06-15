# Интернет-магазин: Микросервисы Заказов и Платежей

Этот проект представляет собой реализацию микросервисной архитектуры для интернет-магазина, состоящую из следующих компонентов:

- **API Gateway**: Отвечает за маршрутизацию входящих запросов к соответствующим микросервисам.
- **Orders Service**: Управляет созданием заказов, их списком и статусами. Реализует паттерн Transactional Outbox для инициирования платежей. Внесены исправления для предотвращения создания заказов с отрицательной или нулевой суммой, а также для корректной сериализации десятичных чисел в ответах API.
- **Payments Service**: Обрабатывает операции, связанные с пользовательскими счетами: создание, пополнение и просмотр баланса. Реализует паттерны Transactional Inbox и Outbox для обеспечения гарантий доставки сообщений и атомарных операций с балансом.
- **Frontend Service**: Простой веб-интерфейс для взаимодействия с микросервисами.

## Технологии

- Python 3.11+
- FastAPI: Для создания RESTful API
- SQLAlchemy: Для работы с базой данных
- SQLite: Для хранения данных
- Uvicorn: ASGI сервер для запуска FastAPI приложений
- Docker & Docker Compose: Для контейнеризации и оркестрации сервисов
- HTML/CSS/JavaScript: Для фронтенд-интерфейса

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <your-repository-url>
cd kpo3_p
```

### 2. Запуск через Docker

Проект использует Docker для запуска всех сервисов. Убедитесь, что у вас установлены Docker и Docker Compose.

#### Быстрый запуск

##### Windows
```bash
start.bat
```

##### Linux/macOS
```bash
chmod +x start.sh  # Только при первом запуске
./start.sh
```

Или вручную:
```bash
docker-compose up --build
```

2. Откройте браузер по адресу `http://localhost:8080`

#### Остановка сервисов

```bash
docker-compose down
```

### 3. Ручной запуск (без Docker)

Каждый сервис можно запустить отдельно.

#### API Gateway
```bash
cd api_gateway
uvicorn main:app --reload --port 8000
```

#### Orders Service
```bash
cd orders_service
uvicorn main:app --reload --port 8002
```

#### Payments Service
```bash
cd payments_service
uvicorn main:app --reload --port 8001
```

#### Frontend Service
```bash
cd frontend_service
python -m http.server 8080
```

## API Эндпоинты

### API Gateway (http://localhost:8000)

- `GET /health`: Проверка работоспособности шлюза
- `GET /docs`: Swagger UI документация

### Orders Service (http://localhost:8002)

- `POST /orders`: Создать новый заказ
- `GET /orders`: Получить список заказов пользователя
- `GET /orders/{order_id}`: Получить статус отдельного заказа
- `POST /orders/payment-status`: Обновить статус заказа по результату оплаты

### Payments Service (http://localhost:8001)

- `POST /accounts`: Создать счёт для пользователя
- `POST /accounts/top-up`: Пополнить счёт пользователя
- `GET /accounts/{user_id}/balance`: Просмотреть баланс счёта
- `POST /payments/process`: Обработка платежа

## Сценарий создания заказа и автооплаты

1. **Пользователь создает заказ** через веб-интерфейс
2. **Orders Service** создаёт заказ и задачу на оплату
3. **Payments Service** обрабатывает платеж
4. **Orders Service** обновляет статус заказа

## Тестирование

### Запуск тестов

```bash
# Orders Service
pytest orders_service/tests/ --cov=orders_service/src

# Payments Service
pytest payments_service/tests/ --cov=payments_service/src

# API Gateway
pytest api_gateway/tests/ --cov=api_gateway/src
```

## Структура проекта

```
kpo3_p/
├── api_gateway/
├── orders_service/
├── payments_service/
├── frontend_service/
├── docker-compose.yml
├── start.bat        # Скрипт запуска для Windows
├── start.sh         # Скрипт запуска для Linux/macOS
└── README.md
``` 