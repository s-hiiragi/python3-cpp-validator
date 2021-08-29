import os
import re
import sys
import argparse
from pathlib import Path
from collections import namedtuple
from typing import NamedTuple


class Token(NamedTuple):
    """
    ソースコードの最小単位であるトークンを表すクラス

    Attributes
    ----------
    tag : str
        以下のいずれか
        pp (preprocessor directives)
        vd (validator directives)
        id (keywords, identifiers)
        num (number literals)
        str (string literals))
        mark (operators)
    str : str
        任意の文字列
    lineno : int
        トークンの行位置
    columnno : int
        トークンの桁位置
    """

    tag: str
    str: str
    lineno: int
    columnno: int

    def __repr__(self):
        #return f"Token('{self.tag}', '{self.str}', {self.lineno}, {self.columnno})"
        #return f"Token({self.tag}:'{self.str}')"
        return f"Token[{self.tag}]'{self.str}'({self.lineno}:{self.columnno})"

    def __str__(self):
        return repr(self)


def tokenize(code):
    code = code.replace('\r\n', '\n')

    tokens = []
    i = 0
    lineno = 1
    linestart = 0

    def columnno():
        return i - linestart + 1

    while i < len(code):
        subcode = code[i:]
        token = None

        # プリプロセッサ命令
        if m := re.match(r'#[^\n]+', subcode):
            token = Token('pp', m.group(), lineno, columnno())
            i += len(m.group())

        # バリデータ命令
        elif m := re.match(r'//![^\n]+', subcode):
            token = Token('vd', m.group()[3:], lineno, columnno())
            i += len(m.group())

        # コメント行
        elif m := re.match(r'//[^\n]+', subcode):
            i += len(m.group())

        # 改行
        elif subcode[0] == '\n':
            i += 1
            lineno += 1
            linestart = i

        # 空白
        elif m := re.match(r'[ \t]+', subcode):
            i += len(m.group())

        # 識別子
        elif m := re.match(r'[_a-zA-Z]\w*', subcode):
            token = Token('id', m.group(), lineno, columnno())
            i += len(m.group())

        # 数値リテラル
        elif m := re.match(r'\d+', subcode):
            token = Token('num', m.group(), lineno, columnno())
            i += len(m.group())

        # 文字列リテラル
        elif m := re.match(r'"(?:[^"]|\\.)*"', subcode):
            token = Token('str', m.group(), lineno, columnno())
            i += len(m.group())

        # 記号
        elif m := re.match(r'\+\+|--|[-+*/%&|^=!<>]=|&&|(?:\|\|)|(<<|>>)=?|->\*?|\.\*|::\*?', subcode):
            token = Token('mark', m.group(), lineno, columnno())
            i += len(m.group())

        else:
            token = Token('mark', subcode[0], lineno, columnno())
            i += 1

        if token:
            tokens.append(token)

    return tokens


ValidateRule = namedtuple('ValidateRule', 'scope_level tag str get_message')


def unused_message(token):
    return f"Variable '{token.str}' cannot be used."


ValidateError = namedtuple('ValidateError', 'message token')


def validate_tokens(tokens):
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

        return 1


if __name__ == '__main__':
    status = main()
    if status:
        sys.exit(status)

