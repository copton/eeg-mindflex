# eeg-mindflex

## How to setup

Below are the instructions to setup the project for local development for each of the supported operating systems.

In each case make sure you have Python 3.10 installed. Then run the commands listed below in the terminal when you are at the root of the repository.

These instructions will allow you to run the application.

```bash
poetry install --with dev
```

### On macOS

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --with macos
```

### On Windows

```bash
C:\Python311\python.exe -m venv .venv
.venv\Scripts\activate
pip install poetry
poetry install --with windows
```

### On Linux

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --with linux
```

## Development Setup

If you want to develop the app locally, run these additional commands:

```bash
poetry install --with dev
pre-commit install --hook-type pre-push
```

This will:
1. Install development dependencies
2. Setup pre-commit hooks to run quality checks before each push.

To run the pre-commit hooks, you can run the following command:

```bash
pre-commit run --all-files
```

### Working with Pre-push Hooks

Quality checks will run automatically before pushing. To run them manually:

```bash
# Run all push-stage checks on all files
pre-commit run --hook-stage push --all-files

# Run all push-stage checks on specific files
pre-commit run --hook-stage push --files path/to/file1.py path/to/file2.py

# Run specific push-stage checks
pre-commit run ruff-format --hook-stage push --all-files
pre-commit run ruff-check --hook-stage push --all-files
pre-commit run mypy --hook-stage push --all-files
pre-commit run pytest --hook-stage push --all-files
```

To skip the checks when pushing (not recommended for final pushes):
```bash
git push --no-verify
```

## How to run the application

Run the following command in the terminal when you are in the root of the repository.

```bash
poetry run app --help
```

This will show you the help message for the application.

To run the application, you need to have the Mindflex connected to your computer.
Let's say the Mindflex is connected to the port `/dev/tty.Mindflex-DevB`. Then you can run the application with the following command:

```bash
poetry run app --live /dev/tty.Mindflex-DevB
```

If you want to record the data to a file, you can use the following command and then see the `recordings` folder for a file with the current date and time in the name:

```bash
poetry run app --live /dev/tty.Mindflex-DevB --record
```
