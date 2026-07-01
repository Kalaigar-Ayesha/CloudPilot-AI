# Stage 1: Build dependencies wheelhouse
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime image
FROM python:3.12-alpine AS runtime

WORKDIR /app

RUN apk add --no-cache libpq libffi openssl && \
    addgroup -S cloudpilot && adduser -S cloudpilot -G cloudpilot

COPY --from=builder /root/.local /home/cloudpilot/.local
COPY . .

# Set paths and non-root execution permissions
ENV PATH=/home/cloudpilot/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

RUN chown -R cloudpilot:cloudpilot /app

USER cloudpilot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/v1/health/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
