# ANBScouts

## Getting started
To run the project, make the following commands:

```shell
git clone git@gitlab.com:aws-all-wallet-surrendered/ANBScouts.git

cd ANBScouts/docker

docker-compose up
```

This will turn the following services on:
- Flask
- Celery
- NGINX
- PostgreSQL
- Redis

> [!IMPORTANT]
> Look through the .env_example to know which variables you need to run.

## Migrations
Currently, migrations are needed because using Gunicorn spawns 4 workers. Therefore, if we use the default SQLAlchemy method:

```python
db.create_all()
```

it will cause a crash due to race conditions between workers. To avoid this, we will use Alembic with the `Flask-Migrate` package.

Ideally, the only migration we need to handle is the first one (already created). However, if you need to modify the schema and create a new migration, you can follow these steps:

1. Delete the `.py` file inside `/migrations/versions`.
2. Create a new migration.

### Steps to Create a New Migration

Since we are using Docker, the process involves additional steps:

1. Modify the database connection in `app.py` to:

   ```python
   # ...
   else f"postgresql://{db_user}:{db_password}@localhost/{db_name}?sslmode=disable"
   # ...
   ```

2. Run the following command inside the `docker` folder:

   ```sh
   docker-compose up postgres
   ```

3. In another terminal, from the root folder, run:

   ```sh
   uv run flask db migrate -m "migration name"
   ```

4. Commit your changes and test that it works (optional)