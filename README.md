_Этот проект представляет собой парсер, который собирает информацию о топ-100 репозиториев GitHub и их активности. Данные сохраняются в базе данных PostgreSQL, а затем предоставляются через API FastAPI._

## Функциональность

### Парсер:
- Ежедневно извлекает список топ-100 репозиториев GitHub по количеству звезд.
- Собирает информацию о каждом репозитории, включая:
  - Имя
  - Владелец
  - Текущая позиция в топе
  - Предыдущая позиция в топе
  - Количество звезд
  - Количество watchers
  - Количество forks
  - Количество открытых issue
  - Язык программирования
- Собирает данные об активности репозиториев, включая:
  - Дату
  - Количество коммитов
  - Список авторов
- Обновляет существующие записи в базе данных или добавляет новые, если репозиторий не найден.
### API FastAPI:
Предоставляет два эндпоинта:
- **/api/repos/top100**: Возвращает список топ-100 репозиториев с подробной информацией.
- **/api/{owner}/{repo}/activity?since={date1}&until={date2}**: Возвращает активность репозитория за указанный период.

## Технологии
- Python 3.12
- FastAPI
- asyncpg (асинхронный драйвер PostgreSQL)
- aiohttp
- Pydantic
- Docker
- Docker Compose
  
# Как запустить?
## Способ 1 - Локальный запуск
### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```
### 2. Настройка подключения к GitHub API и PostgreSQL
Добавьте следующие переменные окружения
```bash
POSTGRES_USER = <логин>
POSTGRES_PASSWORD = <пароль>
POSTGRES_HOST = <хост подключения, по умолчанию ставить "localhost">
POSTGRES_PORT = <порт подключения, по умолчанию ставить 5432>
POSTGRES_DB = <название базы данных>

GITHUB_TOKEN = <токен авторизации GitHub>
```
Узнать как получить токен авторизации можно [ЗДЕСЬ](https://docs.github.com/ru/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on)

### 3. Запуск
+ Для запуска API:
```bash
cd api/
uvicorn main:app --host 0.0.0.0 --port 8000
```
+ Для запуска парсера:
```bash
cd parser/
python main.py
```

## Способ 2 - Docker и Docker Compose
### 1. Объявить необходимые переменные окружения [Как тут](2-настройка-подключения-к-github-api-и-postgresql)
### 2. (по-желанию) настроить dockerfile и docker-compose.yml
### 3. Запуск
+ Для запуска API:
```bash
docker-compose up (для Windows)
docker compose up (для Unix)
```

## Способ 3 - Деплой на Yandex Cloud
Парсер можно развернуть на Yandex Cloud Function при помощи скрипта `deploy_parser_yc.sh`
Для этого:
  1. Необходимо установить и настроить Yandex Cloud CLI согласно [официальной документации](https://yandex.cloud/ru/docs/cli/quickstart#linux_1)
  2. Убедиться что установлен Docker и Docker Compose
  3. Настроить Docker при помощи команды ```yc container registry configure-docker```
  4. Убедиться что пользователь добавлен в [docker-группу](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
  5. Выполнить авторизацию Docker в Yandex Container Registry [любым удобным способом](https://yandex.cloud/en/docs/container-registry/operations/authentication)
  6. Отредактировать скрипт `deploy_parser_yc.sh` установив собсвтенные значения для подключения к БД и ID сервисного аккаунта
  7. Выдать права запуска скрипту и запустить
```bash
chmod +x deploy_parser_yc.sh
./deploy_parser_yc.sh
``` 
