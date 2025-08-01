import unittest

from sql_utils import split_sql_statements, add_schema_to_sql


# noinspection SqlNoDataSourceInspection
class TestSQLLogic(unittest.TestCase):
    def setUp(self):
        self.schema = "myschema"

    def test_insert_select(self):
        sql = "INSERT INTO mytable (id, name) SELECT id, name FROM othertable;"
        expected = f"INSERT INTO {self.schema}.mytable (id, name) SELECT id, name FROM {self.schema}.othertable;"
        result = add_schema_to_sql(sql, self.schema)
        self.assertIn(f"INSERT INTO {self.schema}.mytable", result)
        self.assertIn(f"FROM {self.schema}.othertable", result)

    def test_select_with_comment(self):
        sql = """
        -- 这是一个注释
        SELECT * FROM mytable WHERE id=1; -- 行尾注释
        """
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertIn(f"FROM {self.schema}.mytable", result)

    def test_insert_with_comment(self):
        sql = """
        INSERT INTO mytable (id) VALUES (1); -- 插入数据
        """
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertIn(f"INSERT INTO {self.schema}.mytable", result)

    def test_multiple_statements_with_comments(self):
        sql = """
        -- 创建表
        CREATE TABLE mytable (id INT);
        -- 插入数据
        INSERT INTO mytable (id) VALUES (1);
        """
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 2)
        for stmt in stmts:
            result = add_schema_to_sql(stmt, self.schema)
            self.assertIn(self.schema, result)

    def test_special_sql(self):
        sql = """
        /* 多行注释
        测试 */
        UPDATE mytable SET name='abc' WHERE id=1;
        """
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertIn(f"UPDATE {self.schema}.mytable", result)

    def test_alter_table_change(self):
        sql = "ALTER TABLE t1 CHANGE old_col new_col INT"
        expected = f"ALTER TABLE {self.schema}.t1 CHANGE old_col new_col INT"
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertEqual(result, expected)

    def test_alter_table_modify(self):
        sql = "ALTER TABLE t1 MODIFY COLUMN col INT NULL COMMENT 'test-comment'"
        expected = f"ALTER TABLE {self.schema}.t1 MODIFY COLUMN col INT NULL COMMENT 'test-comment'"
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertEqual(result, expected)

    def test_alter_table_modify_with_comments(self):
        sql = """
        -- modify column comment
        ALTER TABLE t1 MODIFY COLUMN col INT NULL COMMENT 'test-comment'
        """
        expected = f"ALTER TABLE {self.schema}.t1 MODIFY COLUMN col INT NULL COMMENT 'test-comment'"
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        result = add_schema_to_sql(stmts[0], self.schema)
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()