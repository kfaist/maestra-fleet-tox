FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY server/ .
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
