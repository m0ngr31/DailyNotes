# DailyNotes: Keep track of notes and tasks in Markdown

<p align="center">
  <img src="https://i.imgur.com/AI8bd73.png"/>
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