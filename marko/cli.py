#! -*- coding: utf-8 -*-
"""
Command line interfaces
"""
import sys
import importlib
import marko
from argparse import ArgumentParser


def import_class(import_string):
    try:
        module, classname = import_string.rsplit(".", 1)
        cls = getattr(importlib.import_module(module), classname)
    except ValueError:
        sys.exit("Please supply module.classname.")
    except ImportError:
        sys.exit("Cannot import module %s" % module)
    except AttributeError:
        sys.exit("Cannot find class {} in module {}".format(classname, module))
    else:
        return cls


def parse(args):
    parser = ArgumentParser(prog="marko")

    parser.add_argument("-v", "--version", action="version", version=marko.__version__)
    parser.add_argument(
        "-p",
        "--parser",
        type=import_class,
        default="marko.Parser",
        help="Specify another parser class",
    )
    parser.add_argument(
        "-r",
        "--renderer",
        type=import_class,
        default="marko.HTMLRenderer",
        help="Specify another renderer class",
    )
    return parser.parse_args(args)


def main():
    namespace = parse(sys.argv[1:])
    content = sys.stdin.read()
    markdown = marko.Markdown(namespace.parser, namespace.renderer)
    print(markdown(content))


if __name__ == "__main__":
    main()
