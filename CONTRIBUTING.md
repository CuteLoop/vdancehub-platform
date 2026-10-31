# Contributing

Open an issue describing the user behavior and acceptance criteria before a large change. Development
uses test-driven, behavior-focused pull requests.

1. Add a failing test that expresses the behavior or regression.
2. Make the minimum implementation pass.
3. Refactor while keeping the test meaningful.
4. Run `ruff check .`, `mypy apps config`, `python manage.py makemigrations --check`, and `pytest`.

Pull requests must describe permissions and threat-model impact, migrations, verification, and rollback.
Never include real member data, provider access tokens, private video links, or production secrets in
tests, issues, or logs.

