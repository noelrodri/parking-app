Parking app implemented in Flask, creates a default admin super user by default with the credentials (username:- admin@example.com, password- password)

The app allows the Admin to create and delete parking lots and edit parking spots. 
The user can book and release parking spots. 
Both the admin and users have relevant dashboards displaying relevant statistics. 

## Setup

```
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create your `.env` from the committed template, then fill in the blanks:

```
cp .env.example .env
```

Generate `SECRET_KEY` and `SECURITY_PASSWORD_SALT` (two different values) with
`python3 -c "import secrets; print(secrets.token_hex(32))"`. `.env` is
gitignored. Do not run without filling it in -- the code falls back to hardcoded
defaults that are visible in this public repo, and anyone who knows the
SECRET_KEY can forge a session cookie for any account.

Create the database schema, then start the app:

```
export FLASK_APP=app.py
flask db upgrade
python app.py
```

## Database migrations

The schema is owned by Alembic (via Flask-Migrate), not by `db.create_all()`.
`flask db upgrade` must be run before the first start, and again after pulling
any change that touches `models/models.py`. Roles and the default admin are
seeded automatically on start once the tables exist.

After changing a model:

```
flask db migrate -m "what changed"   # review the generated file before committing
flask db upgrade
```

The `migrations/` directory is tracked in git on purpose -- the revision files
are the shared schema history, and every environment must replay the same ones.

`render_as_batch` is enabled in `migrations/env.py` because SQLite cannot
`ALTER TABLE` to add NOT NULL columns; batch mode rebuilds the table instead.
