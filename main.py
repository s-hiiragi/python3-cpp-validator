import os
import re
import sys
import argparse
from pathlib import Path
from collections import namedtuple
from collections.abc import Sequence
from src.tokenize import Token, tokenize

from typing import NamedTuple, Callable


class ValidateRule(NamedTuple):
    scope_level: int
    tag: str
    str: str
    get_message: Callable[[Token], str]


def unused_message(token: Token) -> str:
    return f"Variable '{token.str}' cannot be used."


class ValidateError(NamedTuple):
    message: str
    token: Token


def validate_tokens(tokens: Sequence[Token]) -> list[ValidateError]:
    errors = []

    rules = []
    scope_level = 0
    for token in tokens:
        if token.str == '{':
            scope_level += 1

        elif token.str == '}':
            scope_level -= 1
            # 現在のスコープと同じかより上位のスコープで定義されたルールのみ残す
            rules = [r for r in rules if r.scope_level <= scope_level]

        elif token.tag == 'vd':
            name, args = re.split(r'\s+', token.str, 1)
            args = re.split(r'\s*,\s*', args)

            rule = None
            if name == 'unused':
                for arg in args:
                    rule = ValidateRule(scope_level, 'id', arg, unused_message)

            if rule:
                rules.append(rule)

        else:
            for rule in rules:
                if token.tag == rule.tag and token.str == rule.str:
                    error = ValidateError(rule.get_message(token), token)
                    errors.append(error)

    return errors


def print_validate_error(infile: str, code: str, errors: Sequence[ValidateError]):
    lines = code.replace('\r\n', '\n').split('\n')
    
    for error in errors:
        token = error.token
        prefix = f'{infile.name}:{token.lineno}:{token.columnno}: '

        print(f'{prefix}{error.message}')

        # XXX ^の位置がずれるのでタブを空白1つに置き換える
        error_line = lines[token.lineno - 1].replace('\t', ' ')
        print(f'{prefix}note: {error_line}')

        hat = ' ' * (token.columnno - 1) + '^'
        print(f'{prefix}note: {hat}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    args = parser.parse_args()

    infile = Path(args.infile)

    with open(str(infile)) as f:
        code = f.read()

    tokens = tokenize(code)
    if tokens is None:
        print('ERROR: tokenize was failed')
        return 1

    #print(tokens)

    if errors := validate_tokens(tokens):
        print('ERROR: validate was failed')
        print_validate_error(infile, code, errors)
        return 1


if __name__ == '__main__':
    status = main()
    if status:
        sys.exit(status)

