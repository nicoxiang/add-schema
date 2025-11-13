from functools import lru_cache

from antlr4.InputStream import InputStream
from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.tree.Tree import ParseTreeWalker

import sqlglot

from MySqlLexer import MySqlLexer
from MySqlParser import MySqlParser
from schema_modifier_listener import SchemaModifierListener


def split_sql_statements(sql_content):
    # 使用sqlglot自带的split方法，能正确处理分号、字符串、注释等
    statements = []
    for stmt in sqlglot.transpile(sql_content, read="mysql", pretty=True, comments=False):
        s = stmt.strip()
        if s:
            statements.append(s)
    return statements

def add_schema_to_sql(sql, schema):
    """
    使用 ANTLR MySQL 解析器解析 SQL，并在表名前添加 schema 前缀。
    """
    replacements = _get_table_replacements(sql)

    if not replacements:
        return sql

    # 从后往前替换，避免索引错位
    result = sql
    for start, stop, table_name in sorted(replacements, key=lambda x: -x[0]):
        result = result[:start] + f"{schema}.{table_name}" + result[stop + 1:]
    return result


@lru_cache(maxsize=256)
def _get_table_replacements(sql: str) -> tuple[tuple[int, int, str], ...]:
    """
    解析 SQL，返回所有需要添加 schema 的表的起止位置及原始表名。
    结果使用 LRU 缓存，避免对相同 SQL 重复解析。
    """
    input_stream = InputStream(sql)
    lexer = MySqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()

    parser = MySqlParser(token_stream)
    tree = parser.root()

    listener = SchemaModifierListener()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    return tuple(listener.replacements)