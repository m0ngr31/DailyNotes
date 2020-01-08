FROM nikolaik/python-nodejs:python3.8-nodejs12-alpine

RUN mkdir /app

WORKDIR /app

VOLUME ["/config"]

COPY . .

RUN \
  cd /app && \
  pip install gunicorn && \
  pip install -r requirements.txt

RUN \
  cd /app/app && \
  rm -rf node_modules && \
  npm install node-sass && \
  npm install && \
  npm run build

RUN \
  rm -rf /app/config && \
  ln -s /config /app/config

EXPOSE 5000

ENTRYPOINT ["gunicorn", "server:app", "0.0.0.0:5000"]