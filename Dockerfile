FROM nikolaik/python-nodejs:python3.10-nodejs18

RUN mkdir /app
WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y build-essential libffi-dev && rm -rf /var/lib/apt/lists/*

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