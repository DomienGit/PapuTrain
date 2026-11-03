# Obraz backendu PapuTrain (FastAPI + uvicorn).
# Baza SQLite leży poza kontenerem — ścieżkę ustawia PAPUTRAIN_DB
# (zobacz docker-compose.yml: volume ./data), dzięki temu dane
# przeżywają przebudowanie obrazu.
FROM python:3.12-slim

WORKDIR /app

# Najpierw same zależności — Docker cache'uje warstwę, dopóki
# requirements.txt się nie zmieni (szybkie przebudowy przy zmianach kodu).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Reszta kodu (.dockerignore odsiewa .venv, frontend, .env, bazę).
COPY . .

ENV PAPUTRAIN_DB=/data/app.db

# Uvicorn nasłuchuje na wszystkich interfejsach — w sieci compose
# (od świata chroni go Caddy, kontener nie wystawia portów na host).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
