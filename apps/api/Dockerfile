FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-firebase.txt ./
ARG INSTALL_FIREBASE=false
RUN pip install --no-cache-dir --upgrade pip==26.2.2 && pip install --no-cache-dir -r requirements.txt && if [ "$INSTALL_FIREBASE" = "true" ]; then pip install --no-cache-dir -r requirements-firebase.txt; fi && useradd --uid 10001 --create-home aegis
COPY --chown=aegis:aegis . .
USER aegis
EXPOSE 8000
CMD ["uvicorn", "aegis.main:app", "--host", "0.0.0.0", "--port", "8000"]
