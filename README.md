# gh-automation-base
![GH_Automation_:: version](https://img.shields.io/badge/version-0.1.0-blue)

[![License MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-380/)
[![Poetry](https://img.shields.io/badge/Poetry-1.5-blue)](https://python-poetry.org/docs/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A project base for automating tasks in Python using GitHub actions and an Aiven for PostgreSQL database.

## Setup (quick start)

1. Create a new repository using this repository as a template.
2. Create a new Aiven PostgreSQL service.
3. Copy `.env.example` to `.env` and fill in the values.
4. Install poetry and the dependencies (base + dev) using the following commands:

    ```bash
    pip install poetry
    poetry install --all-extras
    ```

5. Initialize the database using the following command:

    ```bash
    make migration-init migration-apply
    ```

6. Push to GitHub, set the [repo secrets][github-secrets] and enable GitHub actions.
7. This will start populating your database with Quotes (example pipeline).


## Make it your own

### Create your Aiven service

1. Create an Aiven account (or reuse an existing one) at [aiven.io][aiven-io].
2. Create a new PostgreSQL service. You can create a free one if you do not already have one.

### Create your repository

1. Create a new repository using this repository as a template.
2. Set up your [repo secrets][github-secrets] using the values from your Aiven service.

### Set up your local environment

1. Install poetry and the dependencies (base + dev) using the following commands:

    ```bash
    pip install poetry
    poetry install --all-extras
    ```

2. Copy `.env.example` to `.env` and fill in the values, using the values from your Aiven service.

### Adapt the code to your needs

There are four files that will interest you:

- `gh_automation_base/pipelines/quotes.py`: the example pipeline file.
  - Delete this file and create your own pipeline file.
- `gh_automation_base/cli.py`: the CLI entrypoint.
  - Register your own endpoint here. You can delete the `quotes` endpoint.
- `migrations/*`: the database migrations.
  - Declare your tables here. If you do not use the example pipeline, you should delete the `quotes` 
    table migration file before running any migration command.
- `.github/workflows/run-task.yml`: the GitHub action workflow file.
  - Modify the `poetry run auto quotes` command to call your own endpoint instead.
  - Change the [cron schedule][cronguru] to your liking.

### Initialize your database

After having created all the migrations you need (using `make migration-new`), you can initialize your database using the following command:

```bash
make migration-init migration-apply
```

### Set up the GitHub Action

1. Have GitHub call your endpoint in the workflow file [here](./.github/workflows/run-task.yml): `poetry run auto <your-endpoint>`.
2. Push your code to your repository.

[github-secrets]: https://docs.github.com/en/actions/reference/encrypted-secrets
[aiven-io]: http://aiven.io/
[cronguru]: https://crontab.guru/
