import os

import nox

os.environ.update(PDM_IGNORE_SAVED_PYTHON="1")


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
def tests(session):
    session.run("pdm", "install", "-d", external=True)
    session.run("pytest", "tests/")


@nox.session
def benchmark(session):
    session.run("pdm", "install", "-dG", "benchmark", external=True)
    session.run("python", "-m", "tests.benchmark")
