#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import sys
from importlib import import_module
from time import perf_counter

TEST_FILE = "tests/samples/syntax.md"
TIMES = 100

open = functools.partial(open, encoding="utf-8")


def benchmark(package_name):
    def decorator(func):
        def inner():
            try:
                package = import_module(package_name)
            except ImportError:
                return "not available."

            start = perf_counter()
            for _ in range(TIMES):
                func(package)
            end = perf_counter()

            return end - start

        return inner

    return decorator


@benchmark("markdown")
def run_markdown(package):
    with open(TEST_FILE, "r") as fin:
        return package.markdown(fin.read())


@benchmark("mistune")
def run_mistune(package):
    with open(TEST_FILE, "r") as fin:
        return package.markdown(fin.read())


@benchmark("commonmark")
def run_commonmark(package):
    with open(TEST_FILE, "r") as fin:
        return package.commonmark(fin.read())


@benchmark("marko")
def run_marko(package):
    with open(TEST_FILE, "r") as fin:
        return package.convert(fin.read())


@benchmark("mistletoe")
def run_mistletoe(package):
    with open(TEST_FILE, "r") as fin:
        return package.markdown(fin)


@benchmark("markdown_it")
def run_markdown_it(package):
    md = package.MarkdownIt()
    with open(TEST_FILE, "r") as fin:
        return md.render(fin.read())


def run(package_name):
    print(f"{package_name:>15}:  ", end="")
    print(globals()["run_{}".format(package_name.lower())]())


def run_all(package_names):
    prompt = "Running tests with {}...".format(", ".join(package_names))
    print(prompt)
    print("=" * len(prompt))
    for package_name in package_names:
        run(package_name)


def main(*args):
    print("Test document: {}".format(TEST_FILE))
    print("Test iterations: {}".format(TIMES))
    if args[1:]:
        run_all(args[1:])
    else:
        run_all(
            ["markdown", "mistune", "commonmark", "marko", "mistletoe", "markdown_it"]
        )


if __name__ == "__main__":
    main(*sys.argv)
