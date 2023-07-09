# FastAPI Social Network

Practise application for FastAPI

## Running in Docker
### "Prod" version:
```bash
docker compose build
docker compose up
```
### Dev version (with code reload and pgAdmin container):
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```


## Installation (non-docker):

- Create virtualenv if desired
```bash
python3 -m venv venv
source venv/bin/activate
```
- Install as package
```bash
pip install git+https://github.com/Lgmrszd/fastapi-social-network.git
```

### Usage:
Dev:

```bash
uvicorn fastapi_social_network.app:app --reload
```

For prod, export environment variables:

- `SQLALCHEMY_DATABASE_URL`: SQLAlchemy DB connection url (local SQLite DB by default)
- `SECRET_KEY`: Secret Key used for JWT token generation
- `APP_ENV`: `prod` or `dev` (currently does nothing, will be used for checks)

## Running tests:

```bash
pip install -r requirements.testing.txt
python -m pytest
```