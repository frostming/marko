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


@nox.session
def docs(session):
    session.install("pdm", "install", "-G", "doc", external=True)
    session.install("sphinx-autobuild")

    session.run(
        "sphinx-autobuild",
        "docs/",
        "docs/_build/html",
        # Rebuild all files when rebuilding
        "-a",
        # Trigger rebuilds on code changes (for autodoc)
        "--watch",
        "marko",
        # Use a not-common high-numbered port
        "--port",
        "8765",
    )
