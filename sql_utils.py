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