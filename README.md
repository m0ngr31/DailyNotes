# DailyNotes: Keep track of notes and tasks in Markdown

<p align="center">
  <!-- Font-Awesome book-open -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512" width="200px">
    <path style="fill:#6abfb0" d="M542.22 32.05c-54.8 3.11-163.72 14.43-230.96 55.59-4.64 2.84-7.27 7.89-7.27 13.17v363.87c0 11.55 12.63 18.85 23.28 13.49 69.18-34.82 169.23-44.32 218.7-46.92 16.89-.89 30.02-14.43 30.02-30.66V62.75c.01-17.71-15.35-31.74-33.77-30.7zM264.73 87.64C197.5 46.48 88.58 35.17 33.78 32.05 15.36 31.01 0 45.04 0 62.75V400.6c0 16.24 13.13 29.78 30.02 30.66 49.49 2.6 149.59 12.11 218.77 46.95 10.62 5.35 23.21-1.94 23.21-13.46V100.63c0-5.29-2.62-10.14-7.27-12.99z"/>
  </svg>
</p>

Current version: **1.0-beta1**

## Running
The recommended way of running is to pull the image from [Docker Hub](https://hub.docker.com/r/m0ngr31/dailynotes).

### Docker Setup

#### Environment Variables
| Environment Variable | Description | Default |
|---|---|---|
| API_SECRET_KEY | Used to sign API tokens.                                                                                                             | Will be generated automatically if not passed in. |
| DATABASE_URI | Connection string for DB. | Will create and use a SQLite DB if not passed in. |
| DB_ENCRYPTION_KEY | Secret key for encrypting data. Length must be a multiple of 16.<br><br>*Warning*: If changed data will not be able to be decrypted! | Will be generated automatically if not passed in. |


#### Volumes
| Volume Name | Description |
|---|---|
| /app/config | Used to store DB and environment variables. This is not needed if you pass in all of the above environment variables. |


#### Docker Run
By default, the easiest way to get running is:

```bash
docker run -p 5000:5000 -v /config_dir:/app/config m0ngr31/dailynotes
```

## Development setup

### Installing dependencies
You need Python (works on 2 and 3) and Node >= 8 installed

```bash
pip install -r requirements.txt
cd client
npm install
```

### Creating the environment
You can use the environment variables from above, or you can generate new ones by running the following:

```bash
./verify_env.py
```

Keep in mind that since the data is encrypted, if you modify the `DB_ENCRYPTION_KEY` variable, your data will not be accessible anymore.

### Running
During development you need to run the client and server simultaneously

```bash
./run.sh
```

```bash
cd client
npm run serve
```