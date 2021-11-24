FROM nikolaik/python-nodejs:python3.8-nodejs12-alpine

RUN mkdir /app
WORKDIR /app

COPY . .

RUN apk add build-base libffi-dev shadow

RUN \
  addgroup -g 911 abc && \
  adduser -D -H -u 911 -G abc abc && \
  usermod -G users abc

RUN \
  cd /app && \
  pip install -r requirements.txt && \
  chmod +x run.sh && \
  chmod +x verify_env.py && \
  chmod +x verify_data_migrations.py

RUN \
  cd /app/client && \
  npm ci && \
  npm install node-sass && \
  npm run build

USER abc
EXPOSE 5000
ENTRYPOINT "./run.sh"