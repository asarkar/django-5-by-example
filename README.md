My practice code from the book [Django 5 By Example](https://djangobyexample.com/), 5th ed.

[![](https://github.com/asarkar/django-5-by-example/workflows/CI/badge.svg)](https://github.com/asarkar/django-5-by-example/actions)

Official GitHub repo: https://github.com/PacktPublishing/Django-5-By-Example

## Contents
1. [Building a Blog Application](ch01)
2. [Enhancing Your Blog and Adding Social Features](ch02)

## Development

### Environment Setup

**Download all dependencies**
```
% uv sync
```
**Manually activate venv**
```
% source ./.venv/bin/activate
```

**Deactivate venv**
```
% deactivate
```

### Django Management Commands

Because we use `uv` to manage Python execution, any direct invocation of commands such as `python`, 
`django-admin`, or other executables is replaced with `uv run`. This ensures that all tools run 
within the environment managed by `uv`.

Rather than navigating into each project directory to run management commands, we run all commands 
from the **repository root**. To target a specific Django project (e.g., `ch01`, `ch02`, etc.), 
we pass its directory using the `--directory` flag.

For example, what would normally be executed as:
```
ch01% python manage.py migrate
```

becomes:
```
% uv run --directory ch01 manage.py migrate
```

`uv` will "search upwards" from a given directory until it finds `pyproject.toml`, `.venv`, or `uv` 
configuration files. A directory containing any of these files is considered the project root. `uv` 
will use a `.venv/` if found in the root.

Thus, running a command like `uv run --directory ch01 python -c "import sys; print(sys.executable)"` 
doesn't require manual activation of venv.

**Create a new Django project**:
```
django-admin startproject mysite
```

**Create a new Django application**:
```
python manage.py startapp blog
```

**Apply all database migrations**:
```
python manage.py migrate
```

**Create migrations**:
```
python manage.py makemigrations blog
```

**View the SQL statements that will be executed with the first migration**:
```
python manage.py sqlmigrate blog 0001
```

**Run the Django development server**:
```
python manage.py runserver
```

**Run the development server specifying host/port and settings file**:
```
python manage.py runserver 127.0.0.1:8001 --settings=mysite.settings
```

**Run the Django shell**:
```
python manage.py shell
```

**Create a superuser**:
```
python manage.py createsuperuser
```

**Dump the database into a JSON file**:
```
python manage.py dumpdata auth blog --indent 2 > blog/fixtures/blog.json
```

**Seed the database from a JSON file**:
```
python manage.py loaddata blog/fixtures/blog.json
```

**Delete all data from all tables**:
```
python manage.py flush --noinput
```

**Run custom management command**:
```
python manage.py seed_users
```

### Testing

**Run tests**
```
% ./.github/run.sh <chapter_directory>
```
