FROM nikolaik/python-nodejs:python3.8-nodejs16-alpine

RUN mkdir /app
WORKDIR /app

COPY . .

RUN apk add build-base libffi-dev

RUN \
  cd /app && \
  pip install -r requirements.txt && \
  chmod +x run.sh && \
  chmod +x verify_env.py && \
  chmod +x verify_data_migrations.py

RUN \
  cd /app/client && \
  npm ci && \
  npm run build

EXPOSE 5000
ENTRYPOINT ["./run.sh"]