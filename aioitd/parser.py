import re
from html.parser import HTMLParser
from html import escape
from aioitd import Monospace, Bold, Spoiler, Strike, Italic, Link, Underline
from typing import TypedDict

TAGS = {
    "pre": Monospace,
    "code": Monospace,
    "b": Bold,
    "strong": Bold,
    "i": Italic,
    "em": Italic,
    "spoiler": Spoiler,
    "sp": Spoiler,
    "s": Strike,
    "del": Strike,
    "strike": Strike,
    "ins": Underline,
    "u": Underline,
    "a": Link,
    "mb": Bold,
    "mi": Italic,
    "ms": Strike,
    "mu": Underline,
    "mpre": Monospace,
    "msp": Spoiler,
    "ma": Link
}

LINK = ["a", 'ma']


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = ""
        self.spans = []
        self.starts = {}
        for key in TAGS:
            self.starts[key] = []

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS:
            raise ValueError(f"tag <{tag}> not supported")

        if tag not in LINK:
            self.starts[tag].append(len(self.result))
        else:
            href = None
            for attr, value in attrs:
                if attr == 'href':
                    href = value
            self.starts[tag].append((len(self.result), href))

    def handle_endtag(self, tag):
        if tag not in TAGS:
            raise ValueError(f"tag <{tag}> not supported")
        if len(self.starts[tag]) == 0:
            return

        if tag not in LINK:
            start = self.starts[tag].pop()
            self.spans.append(TAGS[tag](length=len(self.result) - start, offset=start))
        else:
            start, url = self.starts[tag].pop()
            self.spans.append(Link(
                length=len(self.result) - start,
                offset=start,
                url=url if url is not None else self.result[start:]
            ))

    def handle_data(self, data):
        self.result += data
        print("Data     :", data)


class ParseResult(TypedDict):
    content: str
    spans: list[Monospace | Strike | Underline | Bold | Italic | Spoiler | Link]


def parse_html(content: str) -> ParseResult:
    r"""Парсит html

    Доступные теги, и соответствующие им spans

    "pre":      Monospace

    "code":     Monospace

    "b":        Bold

    "strong":   Bold

    "i":        Italic

    "em":       Italic

    "spoiler":  Spoiler

    "sp":       Spoiler

    "s":        Strike

    "del":      Strike

    "strike":   Strike

    "ins":      Underline

    "u":        Underline

    "a":        Link

    <а href="https://yu.ru">яндекс</а>

    Если явно не указан href, вместо него будет взято содержимое тега:

    <а>https://yu.ru</а>

    Args:
        content: строка для парсинга

    Returns:
        dict: {"content": текст без тегов, "spans": форматирование итд.com}
    """
    parser = MyHTMLParser()
    parser.feed(content)
    return {
        "content": parser.result,
        "spans": parser.spans,
    }


DELIMITERS = {
    '**': "mb",
    '*': "mi",
    '~~': "ms",
    '__': "mu",
    '`': "mpre",
    '||': "msp",
}


def _split_with_delimiters(s: str):
    escaped_delimiters = [re.escape(d) for d in sorted(DELIMITERS.keys(), key=len, reverse=True)]
    link_pattern = r'\[[^\]]+\]\([^\)]*\)'
    pattern = '(' + '|'.join([r'\\.', link_pattern] + escaped_delimiters) + ')'
    return list(filter(len, re.split(pattern, s)))


def md_to_html(s: str) -> str:
    r"""
    Переводит markdown в html теги

    \**жирный**, \*курсив*, \~~зачёркнутый~~, \_\_подчёркнутый__, \`моноширный`, \||спойлер||

    Теги могут пересекаться, например: \_\_111\*1234__32342*

    Теги могут быть вложенными: \_\_1231\*1323*__

    \[текст ссылки](url)

    Внутри ссылки остальные теги не парсятся


    Если url не указан, за него будет взят текст ссылки, то есть:

    \[текст ссылки]() = \[текст ссылки](текст ссылки)

    используйте \\ для экранирования символов

    Args:
        s: markdown строка

    Returns:
        str: markdown теги заменены на html
    """
    starts = {}
    result = ""
    for token in _split_with_delimiters(s):
        if token[0] == '\\':
            result += token[1]
        elif token in starts:
            del starts[token]
            result += f"</{DELIMITERS[token]}>"
        elif token in DELIMITERS:
            starts[token] = len(result)
            result += f"<{DELIMITERS[token]}>"
        elif match := re.match(r'\[([^\]]+)\]\(([^\)]*)\)', token):
            text = match.group(1)
            url = match.group(2)
            if len(url) == 0:
                url = text
            result += f"<ma href=\"{url}\">{text}</ma>"
        else:
            result += token
    return result


def parse_md(content: str) -> ParseResult:
    r"""
    Парсит markdown.

    \**жирный**, \*курсив*, \~~зачёркнутый~~, \_\_подчёркнутый__, \`моноширный`, \||спойлер||

    Теги могут пересекаться, например: \_\_111\*1234__32342*

    Теги могут быть вложенными: \_\_1231\*1323*__

    \[текст ссылки](url)

    Внутри ссылки остальные теги не парсятся


    Если url не указан, за него будет взят текст ссылки, то есть:

    \[текст ссылки]() = \[текст ссылки](текст ссылки)

    используйте \\ для экранирования символов

    Args:
        content: строка для парсинга

    Returns:
        dict: {"content": текст без тегов, "spans": форматирование итд.com}

    """
    return parse_html(md_to_html(escape(content)))


def parse(content: str) -> ParseResult:
    r"""Парсит html и markdown

    ## html

    Доступные теги, и соответствующие им spans

    "pre":      Monospace

    "code":     Monospace

    "b":        Bold

    "strong":   Bold

    "i":        Italic

    "em":       Italic

    "spoiler":  Spoiler

    "sp":       Spoiler

    "s":        Strike

    "del":      Strike

    "strike":   Strike

    "ins":      Underline

    "u":        Underline

    "a":        Link

    <а href="https://yu.ru">яндекс</а>

    Если явно не указан href, вместо него будет взято содержимое тега:

    <а>https://yu.ru</а>

    ## markdown

    \**жирный**, \*курсив*, \~~зачёркнутый~~, \_\_подчёркнутый__, \`моноширный`, \||спойлер||

    Теги могут пересекаться, например: \_\_111\*1234__32342*

    Теги могут быть вложенными: \_\_1231\*1323*__

    \[текст ссылки](url)

    Внутри ссылки остальные теги не парсятся


    Если url не указан, за него будет взят текст ссылки, то есть:

    \[текст ссылки]() = \[текст ссылки](текст ссылки)

    используйте \\ для экранирования символов

    Args:
        content: строка для парсинга

    Returns:
        dict: {"content": текст без тегов, "spans": форматирование итд.com}
    """
    return parse_html(md_to_html(content))


__all__ = ["ParseResult", "parse", "parse_md", "parse_html"]
