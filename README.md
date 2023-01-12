# FastAPI Social Network

Practise application for FastAPI

## Installation:

1. Create virtualenv if desired
2.
```shell
pip install git+https://github.com/Lgmrszd/fastapi-social-network.git
```


### Usage:
Dev:

```shell
uvicorn fastapi_social_network.app:app --reload
```

For prod, export environment variables:

- `SQLALCHEMY_DATABASE_URL`: SQLAlchemy DB connection url (local SQLite DB by default)
- `SECRET_KEY`: Secret Key used for JWT token generation
- `APP_ENV`: `prod` or `dev` (currently does nothing, will be used for checks)