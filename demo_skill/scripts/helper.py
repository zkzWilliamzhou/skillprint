"""Demo helper used as a capability-detection fixture (never executed by tests)."""


def read_config(path):
    with open(path, "r") as handle:
        return handle.read()


def write_report(path, text):
    with open(path, "w") as handle:
        handle.write(text)


def run_command(command):
    import subprocess

    return subprocess.run(command, capture_output=True, text=True)


def fetch(url):
    import requests

    return requests.get(url, timeout=5)
