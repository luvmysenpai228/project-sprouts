# GreenCounter

## Запуск Backend (Docker)
Для проверки работы ML модели подсчет ростков требуется добавить модель seedlings.pt (файл Назара best.pt) в директорию backend/src/ml/weights

Выполняется командами:
```sh
cd ci
cp .env.dist .env
docker compose up
# после запуска backend контейнера ввести в другой консоли:
docker compose exec backend python manage.py migrate
```