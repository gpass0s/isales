FROM python:3.7

RUN pip install --no-cache-dir pipenv

WORKDIR /app

COPY Pipfile ./
COPY Pipfile.lock ./
COPY setup.py ./

RUN pipenv lock -r > requirements.txt \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

COPY  isales/ ./isales/