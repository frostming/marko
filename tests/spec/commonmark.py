import re
import sys
import codecs
import json
import importlib
from traceback import print_tb
from argparse import ArgumentParser
from .normalize import normalize_html

SPECS = {
    'commonmark': ('tests/spec/commonmark.json', 'marko:markdown'),
    'gfm': ('tests/spec/gfm.json', 'marko.ext.gfm:markdown')
}


def run_tests(
    test_entries, markdown, start=None, end=None, quiet=False, verbose=False
):
    start = start or 0
    end = end or sys.maxsize
    results = [
        run_test(test_entry, markdown, quiet)
        for test_entry in test_entries
        if test_entry['example'] >= start
        and test_entry['example'] <= end
    ]
    if verbose:
        print_failure_in_sections(results)
    fails = len(list(filter(lambda x: not x[0], results)))
    if fails:
        print('failed:', fails)
        print(' total:', len(results))
    else:
        print('All tests passing.')
    return not fails


def run_test(test_entry, markdown, quiet=False):
    test_case = test_entry['markdown']
    try:
        output = markdown(test_case)
        success = normalize_html(test_entry['html']) == normalize_html(output)
        if not success and not quiet:
            print_test_entry(test_entry, output)
        return success, test_entry['section']
    except Exception as exception:
        if not quiet:
            print_exception(exception, test_entry)
        return False, test_entry['section']


def load_tests(flavor):
    assert flavor.lower() in SPECS
    specfile, parser = SPECS[flavor.lower()]
    with codecs.open(specfile, 'r', encoding='utf-8') as f:
        tests = json.load(f)
    module, func = parser.split(':')
    parse_func = getattr(importlib.import_module(module), func)
    return tests, parse_func


def get_tests(specfile):
    line_number = 0
    start_line = 0
    end_line = 0
    example_number = 0
    markdown_lines = []
    html_lines = []
    state = 0  # 0 regular text, 1 markdown example, 2 html output
    headertext = ''
    tests = []

    header_re = re.compile('#+ ')

    with open(specfile, 'r', encoding='utf-8', newline='\n') as specf:
        for line in specf:
            line_number = line_number + 1
            l = line.strip()
            if l.startswith("`" * 32 + " example"):
                state = 1
            elif state == 2 and l == "`" * 32:
                state = 0
                example_number = example_number + 1
                end_line = line_number
                tests.append({
                    "markdown": ''.join(markdown_lines).replace('→', "\t"),
                    "html": ''.join(html_lines).replace('→', "\t"),
                    "example": example_number,
                    "start_line": start_line,
                    "end_line": end_line,
                    "section": headertext})
                start_line = 0
                markdown_lines = []
                html_lines = []
            elif l == ".":
                state = 2
            elif state == 1:
                if start_line == 0:
                    start_line = line_number - 1
                markdown_lines.append(line)
            elif state == 2:
                html_lines.append(line)
            elif state == 0 and re.match(header_re, line):
                headertext = header_re.sub('', line).strip()
    print(json.dumps(tests, ensure_ascii=True, indent=2))
    return 0


def locate_section(section, tests):
    start = None
    end = None
    for test in tests:
        if re.search(section, test['section'], re.IGNORECASE):
            if start is None:
                start = test['example']
        elif start is not None and end is None:
            end = test['example'] - 1
            return start, end
    if start:
        return start, tests[-1]['example'] - 1
    raise RuntimeError("Section '{}' not found, aborting.".format(section))


def print_exception(exception, test_entry):
    print_test_entry(test_entry, '-- exception --', fout=sys.stderr)
    print(exception.__class__.__name__ + ':', exception, file=sys.stderr)
    print('Traceback: ', file=sys.stderr)
    print_tb(exception.__traceback__)


def print_test_entry(test_entry, output, fout=sys.stdout):
    print('example: ', repr(test_entry['example']), file=fout)
    print('markdown:', repr(test_entry['markdown']), file=fout)
    print('html:    ', repr(test_entry['html']), file=fout)
    print('output:  ', repr(output), file=fout)
    print(file=fout)


def print_failure_in_sections(results):
    section = results[0][1]
    failed = 0
    total = 0
    for result in results:
        if section != result[1]:
            if failed:
                section_str = "Failed in section '{}':".format(section)
                result_str = "{:>3} / {:>3}".format(failed, total)
                print('{:70} {}'.format(section_str, result_str))
            section = result[1]
            failed = 0
            total = 0
        if not result[0]:
            failed += 1
        total += 1
    if failed:
        section_str = "Failed in section '{}':".format(section)
        result_str = "{:>3} / {:>3}".format(failed, total)
        print('{:70} {}'.format(section_str, result_str))
    print()


def main():
    parser = ArgumentParser(description="Custom script for running Commonmark tests.")
    parser.add_argument(
        'start',
        type=int,
        nargs='?',
        default=None,
        help="Run tests starting from this position.",
    )
    parser.add_argument(
        'end', type=int, nargs='?', default=None, help="Run tests until this position."
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        help="Output failure count in every section.",
    )
    parser.add_argument(
        '-q',
        '--quiet',
        dest='quiet',
        action='store_true',
        help="Suppress failed test entry output.",
    )
    parser.add_argument(
        '-s',
        '--section',
        dest='section',
        default=None,
        help="Only run tests in specified section.",
    )
    parser.add_argument(
        '-f',
        '--flavor',
        dest='tests',
        type=load_tests,
        default='commonmark',
        help='Specify markdown flavor name.',
    )
    parser.add_argument(
        '--dump',
        dest='spec',
        help='Dump spec.txt to spec.json'
    )
    args = parser.parse_args()

    start = args.start
    end = args.end
    verbose = args.verbose
    quiet = args.quiet
    tests, markdown = args.tests
    if args.spec:
        sys.exit(get_tests(args.spec))
    if args.section is not None:
        start, end = locate_section(args.section, tests)

    if not run_tests(tests, markdown, start, end, quiet, verbose):
        sys.exit(1)


if __name__ == '__main__':
    main()
