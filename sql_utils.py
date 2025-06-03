import re
from sqlglot import parse_one, exp
import sqlglot

def split_sql_statements(sql_content):
    # 使用sqlglot自带的split方法，能正确处理分号、字符串、注释等
    stmts = []
    for stmt in sqlglot.transpile(sql_content, read="mysql", pretty=False, into="statements"):
        s = stmt.strip()
        if s:
            stmts.append(s)
    return stmts

def add_schema_to_sql(sql, schema):
    try:
        tree = parse_one(sql, read="mysql")
    except Exception:
        # 解析失败，直接用正则兜底
        return add_schema_to_sql_by_regex(sql, schema)

    def _add_schema_to_table(table):
        if isinstance(table, exp.Table):
            if not table.args.get("db"):
                table.set("db", exp.Identifier(this=schema))
        return table

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

def add_schema_to_sql_by_regex(sql, schema):
    # 兜底正则处理，适用于无法被sqlglot解析的SQL
    # 只处理常见的 DML/DDL 语句
    patterns = [
        (r"(?i)(?<!ON\s)UPDATE\s+(`?\w+`?)", lambda m: f"UPDATE {schema}.{m.group(1)}"),
        (r"(?i)(FROM|JOIN|INTO)\s+(`?\w+`?)", lambda m: f"{m.group(1)} {schema}.{m.group(2)}"),
        (r"(?i)(CREATE|ALTER|DROP)\s+(TABLE|VIEW|TRIGGER|PROCEDURE|FUNCTION)\s+(`?\w+`?)",
         lambda m: f"{m.group(1)} {m.group(2)} {schema}.{m.group(3)}"),
        (r"(?i)(INSERT\s+INTO)\s+(`?\w+`?)", lambda m: f"{m.group(1)} {schema}.{m.group(2)}"),
    ]
    modified_sql = sql
    for pat, repl in patterns:
        modified_sql = re.sub(pat, repl, modified_sql)
    return modified_sql