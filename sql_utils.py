import re

import sqlglot
from sqlglot import parse_one, exp

from sql_exceptions import UnsupportedSQLError


def split_sql_statements(sql_content):
    # 使用sqlglot自带的split方法，能正确处理分号、字符串、注释等
    statements = []
    for stmt in sqlglot.transpile(sql_content, read="mysql", pretty=True, comments=False):
        s = stmt.strip()
        if s:
            statements.append(s)
    return statements

def add_schema_to_sql(sql, schema):
    tree = parse_one(sql, read="mysql")

    if isinstance(tree, exp.Command):
        manually_modify_result =  modify_sql_manually(sql, schema)
        if manually_modify_result is not None:
            return manually_modify_result
        else:
            raise UnsupportedSQLError("SQL语法暂未支持")

    def _add_schema_to_table(table_obj):
        if isinstance(table_obj, exp.Table):
            if not table_obj.args.get("db"):
                table_obj.set("db", exp.Identifier(this=schema))
        return table_obj

    # 遍历所有Table节点
    for table in tree.find_all(exp.Table):
        _add_schema_to_table(table)

    # 处理CREATE/ALTER/DROP等DDL语句的对象名
    for node in tree.find_all(exp.Create):
        if isinstance(node.this, exp.Table) and not node.this.args.get("db"):
            node.this.set("db", exp.Identifier(this=schema))
    for node in tree.find_all(exp.Alter):
        if isinstance(node.this, exp.Table) and not node.this.args.get("db"):
            node.this.set("db", exp.Identifier(this=schema))
    for node in tree.find_all(exp.Drop):
        if isinstance(node.this, exp.Table) and not node.this.args.get("db"):
            node.this.set("db", exp.Identifier(this=schema))

    return tree.sql(dialect="mysql")

def modify_sql_manually(sql: str, schema: str) -> str | None:
    # 去除换行和多余空白
    sql_clean = ' '.join(sql.strip().split())

    # 只要包含 ALTER TABLE 并至少包含 MODIFY COLUMN / CHANGE / ADD COLUMN 就认为是需要处理的
    pattern = r"(?i)^ALTER\s+TABLE\s+(`?\w+`?)\s+.*?\b(MODIFY\s+COLUMN|CHANGE|ADD\s+COLUMN|DROP\s+COLUMN)\b"

    if re.match(pattern, sql_clean):
        # 插入 schema 到 ALTER TABLE 后的表名中
        modified_sql = re.sub(
            r"(?i)(ALTER\s+TABLE\s+)(`?\w+`?)",
            lambda m: f"{m.group(1)}{schema}.{m.group(2)}",
            sql_clean,
            count=1
        )
        return modified_sql
    return None