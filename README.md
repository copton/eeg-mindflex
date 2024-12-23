# eeg-mindflex

## How to setup 

Below are the instructions to setup the project for local development for each of the supported operating systems.

In each case make sure you have Python 3.10 installed. Then run the commands listed belowin the terminal when you are in the root of the repository.

These instructions will allow you to run the application. If you also want to develop the app locally, you additionally need to run the following command at the end of the instructions:

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

## How to run the application

Run the following command in the terminal when you are in the root of the repository.

```bash
cd app
python main.py --help
```

This will show you the help message for the application.

To run the application, you need to have the Mindflex connected to your computer.
Let's say the Mindflex is connected to the port `/dev/tty.Mindflex-DevB`. Then you can run the application with the following command:

```bash
python main.py --live /dev/tty.Mindflex-DevB
```

If you want to record the data to a file, you can use the following command and then see the `recordings` folder for a file with the current date and time in the name:

```bash
python main.py --live /dev/tty.Mindflex-DevB --record 
```


