### Настройка
# Данные для подключения к PostgreSQL
POSTGRES_USER="postgres"
POSRGRES_PASSWORD="postgres"
POSTGRES_HOST="0.0.0.0"
POSTGRES_PORT="5432"

# Yandex Cloud
SERVICE_ACCOUNT_ID="YOUR_SERVICE_ACCOUNT_ID"	# ID сервисного аккаунта

REGISTRY_ID=""                  # Оставьте пустым, чтобы создать новый реестр Docker-образов
REGISTRY_NAME="YOUR_REGISTRY_NAME"        # Название реестра хранения Docker-образов

### Логика работы

# Если REGISTRY_ID не указан (пустой) - то создает новый реестр и присваивает REGISTRY_ID
if [ -z "$REGISTRY_ID" ]; then
        REGISTRY_ID=$(yc container registry create --name "testjson" --format json | jq -r ".id")       
fi

# Собирает образ с парсером
docker build -t parser-image ./parser

# Устанавливает тег для собранного образа
docker tag parser-image cr.yandex/$REGISTRY_ID/parser-image:latest
# Выгружает образ в реестр YC
docker push cr.yandex/$REGISTRY_ID/parser-image:latest

# Создание YC функции
yc serverless function create --name=parser-function

# Создание версии функции на основе Docker-образа
yc serverless function version create \
        --function-name=parser-function \
        --runtime python312 \
        --entrypoint main.handler \
        --execution-timeout 5m \
        --memory 128m \
        --environment REGISTRY_ID=$REGISTRY_ID \
	--environment POSTGRES_USER=$POSTGRES_USER \
	--environment POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
	--environment POSTGRES_HOST=$POSTGRES_HOST \
	--environment POSTGRES_PORT=$POSTGRES_PORT \
        --source-path ./parser

# Создание триггера функции для запуска раз в день
yc serverless trigger create timer \
        --name daily-trigger \
        --cron-expression '0 0 * * ? *' \
        --invoke-function-name parser-function \
        --invoke-function-service-account-id $SERVICE_ACCOUNT_ID
