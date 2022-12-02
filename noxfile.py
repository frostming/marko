import os

import nox

os.environ.update(PDM_IGNORE_SAVED_PYTHON="1")


@nox.session(python=["3.6", "3.8", "3.9", "3.10"])
def tests(session):
    session.run("pdm", "install", "-d", external=True)
    session.run("pytest", "tests/")


@nox.session
def benchmark(session):
    session.run("pdm", "install", "-dG", "benchmark", external=True)
    session.run("python", "-m", "tests.benchmark")
