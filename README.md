# gh-automation-funda
![GH_Automation_:: version](https://img.shields.io/badge/version-0.1.0-blue)

[![License MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-380/)
[![Poetry](https://img.shields.io/badge/Poetry-1.5-blue)](https://python-poetry.org/docs/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Funda.nl automation using GitHub Actions and Aiven for PostgreSQL.

See [gh-automation-base][gh-automation-base] for more information.

## Usage

### 1. Create a new Google Sheet

This Google Sheet is used to control the dynamic settings of the automation.
This way, you can change the settings at any time without having to change the code.

It should contain a sheet with the following content (for example):

| area                     | object_type              | price_min | price_max | days_old |
|--------------------------|--------------------------|-----------|-----------|----------|
| `["Amsterdam"]`          | `["apartment"]`          | `500000`  | `1000000` | `3`      |
| `["Almere", "Utrecht"]`  | `["house", "apartment"]` | `300000`  | `500000`  | `3`      |

> Do not include the backticks in the actual sheet.

In the above example, the automation will search for apartments in Amsterdam that are 
between 500,000 and 1,000,000 euros and are no older than 3 days, as well as houses or apartments
in Almere and Utrecht that are between 300,000 and 500,000 euros and are no older than 3 days.

To be noted that the `days_old` is only important for the first iteration of the automation.
If the automation runs every N minutes, then most of the properties will be redundant, as they
will have been found in the previous iteration. A small value is recommended, to avoid
parsing a lot of useless properties.

### 2. Add your Google Sheet to the automation

If the URL of your Google Sheet is 
```
https://docs.google.com/spreadsheets/d/12345678901-abcdefghijklmnopqrstuv1234_56789/edit#gid=9876543210
```

then the `SHEET_ID` is `12345678901-abcdefghijklmnopqrstuv1234_56789` and the `GID` is `9876543210`.

In `.env`, add the following:

```dotenv
GH_AUTO_GOOGLE_SHEETS_1_SHEET_ID=12345678901-abcdefghijklmnopqrstuv1234_56789
GH_AUTO_GOOGLE_SHEETS_1_GID=9876543210
GH_AUTO_GOOGLE_SHEETS_1_MODEL=gh_automation_funda.persistence.settings.FundaSetting
```


[gh-automation-base]: https://github.com/Mulugruntz/gh-automation-base
