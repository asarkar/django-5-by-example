My practice code from the book [Django 5 By Example](https://djangobyexample.com/), 5th ed.

[![](https://github.com/asarkar/django-5-by-example/workflows/CI/badge.svg)](https://github.com/asarkar/django-5-by-example/actions)

Official GitHub repo: https://github.com/PacktPublishing/Django-5-By-Example

## Contents
- **Blog Application** (chapters 1-3): Create a complete blog application

## Development

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

**Run tests**
```
% ./.github/run.sh <directory>
```

`uv` will "search upwards" from a given directory until it finds `pyproject.toml`, `.venv`, or `uv` 
configuration files. A directory containing any of these files is considered the project root. `uv` 
will use a `.venv/` if found in the root.

Thus, running a command like `uv run --directory ch01 python -c "import sys; print(sys.executable)"` 
doesn't require manual activation of venv.
