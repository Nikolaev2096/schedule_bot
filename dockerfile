FROM python:3.13-slim

WORKDIR /bot

RUN pip install poetry 

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-root

COPY . .

CMD ["python", "main.py"]