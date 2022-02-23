import re
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


def tokenize(code: str) -> list[Token]:
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

        # ブロックコメント
        elif m := re.match(r'/\*', subcode):
            i += 2

            while i < len(code):
                subcode = code[i:]

                if re.match(r'\*/', subcode):
                    i += 2
                    break
                elif subcode[0] == '\n':
                    i += 1
                    lineno += 1
                    linestart = i
                else:
                    i += 1

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

        # 記号 (3文字)
        elif m := re.match(r'->\*|<<=|>>=', subcode):
            token = Token('mark', m.group(), lineno, columnno())
            i += len(m.group())

        # 記号 (2文字)
        elif m := re.match(r'->|\+\+|--|\.\*|<<|>>|[<>=!+\-*/%&^|]=|&&|\|\|', subcode):
            token = Token('mark', m.group(), lineno, columnno())
            i += len(m.group())

        # 記号 (1文字)
        elif m := re.match(r'[()[\]{}.,:?+\-*/%~&^|=!]', subcode):
            token = Token('mark', m.group(), lineno, columnno())
            i += len(m.group())

        else:
            raise Exception(f"Unknown character '{subcode[0]}' at {lineno}:{columnno()}")

        if token:
            tokens.append(token)

    return tokens

