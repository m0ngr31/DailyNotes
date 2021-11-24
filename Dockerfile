FROM nikolaik/python-nodejs:python3.8-nodejs12-alpine

RUN mkdir /app
WORKDIR /app

COPY . .

RUN apk add build-base libffi-dev shadow sudo

RUN \
  groupmod -g 1000 users && \
  useradd -u 911 -U -s /bin/false abc && \
  usermod -G users abc && \
  echo "abc ALL=(ALL) ALL" > /etc/sudoers.d/abc && chmod 0440 /etc/sudoers.d/abc

RUN \
  cd /app && \
  pip install -r requirements.txt && \
  chmod +x run.sh && \
  chmod +x verify_env.py && \
  chmod +x verify_data_migrations.py

RUN \
  cd /app/client && \
  npm ci && \
  npm rebuild node-sass && \
  npm run build

USER abc
EXPOSE 5000
ENTRYPOINT "./run.sh"