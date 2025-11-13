from antlr4 import *
from MySqlParserListener import MySqlParserListener
from MySqlParser import MySqlParser


class SchemaModifierListener(MySqlParserListener):
    """
    收集所有未带 schema 的表名在原始 SQL 文本中的位置及原始表名。
    """

    def __init__(self):
        self.replacements: list[tuple[int, int, str]] = []  # (start_idx, end_idx, table_name)

    def enterTableName(self, ctx: MySqlParser.TableNameContext):
        # 获取表名 token
        table_name = ctx.getText()

        # 如果已经有 schema（如 mydb.table），则跳过
        if '.' in table_name:
            return

        # 获取 token 位置
        start = ctx.start.start
        stop = ctx.stop.stop

        # 记录替换
        self.replacements.append((start, stop, table_name))

