import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from sql_utils import (
    split_sql_statements,
    add_schema_to_sql,
)

class MySQLAddSchemaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MySQL Add Schema工具")
        self.geometry("800x600")
        self.selected_file = ""
        self.selected_schemas = []
        self.schema_vars = []
        self.schemas = []
        self.create_widgets()
        self.load_schemas()

    def create_widgets(self):
        # 文件选择按钮
        self.file_btn = tk.Button(self, text="选择SQL文件", font=("Arial", 12), height=2, command=self.select_file)
        self.file_btn.pack(fill=tk.X, padx=10, pady=10)

        # schema选择区域
        self.schema_frame = ttk.LabelFrame(self, text="选择Schema")
        self.schema_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.schema_canvas = tk.Canvas(self.schema_frame)
        self.schema_scrollbar = ttk.Scrollbar(self.schema_frame, orient="vertical", command=self.schema_canvas.yview)
        self.schema_inner = tk.Frame(self.schema_canvas)
        self.schema_inner.bind(
            "<Configure>",
            lambda e: self.schema_canvas.configure(
                scrollregion=self.schema_canvas.bbox("all")
            )
        )
        self.schema_canvas.create_window((0, 0), window=self.schema_inner, anchor="nw")
        self.schema_canvas.configure(yscrollcommand=self.schema_scrollbar.set)
        self.schema_canvas.pack(side="left", fill="both", expand=True)
        self.schema_scrollbar.pack(side="right", fill="y")

        # 生成按钮
        self.confirm_btn = tk.Button(self, text="生成SQL", font=("Arial", 12), height=2, bg="#4CAF50", fg="black", command=self.generate_sql)
        self.confirm_btn.pack(fill=tk.X, padx=10, pady=10)

    def show_warning(self, message):
        messagebox.showwarning("警告", message)

    def select_file(self):
        filetypes = [("SQL files", "*.sql"), ("All files", "*.*")]
        file_name = filedialog.askopenfilename(title="选择SQL文件", filetypes=filetypes)
        if file_name:
            self.selected_file = file_name
            self.file_btn.config(text="已选择: " + os.path.basename(file_name))

    def load_schemas(self):
        config_path = os.path.expanduser("~/schemas.conf")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    schema = line.strip()
                    if schema:
                        var = tk.BooleanVar()
                        cb = tk.Checkbutton(self.schema_inner, text=schema, variable=var, anchor="w")
                        cb.pack(fill=tk.X, padx=5, pady=2, anchor="w")
                        self.schema_vars.append(var)
                        self.schemas.append(schema)

    def generate_sql(self):
        import re
        if not self.selected_file:
            self.show_warning("请先选择SQL文件！")
            return

        selected_schemas = [schema for var, schema in zip(self.schema_vars, self.schemas) if var.get()]
        if not selected_schemas:
            self.show_warning("请至少选择一个Schema！")
            return

        try:
            with open(self.selected_file, "r", encoding="utf-8") as f:
                sql_content = f.read()
        except Exception:
            self.show_warning("无法打开SQL文件！")
            return

        sql_statements = split_sql_statements(sql_content)

        output_file_name = re.sub(r"\.sql$", "_generated.sql", self.selected_file, flags=re.IGNORECASE)
        try:
            with open(output_file_name, "w", encoding="utf-8") as out:
                for schema in selected_schemas:
                    for stmt in sql_statements:
                        if stmt.strip():
                            new_sql = add_schema_to_sql(stmt, schema)
                            out.write(new_sql.strip() + ";\n\n")
            messagebox.showinfo("成功", "文件生成成功！\n输出文件: " + output_file_name)
        except Exception:
            self.show_warning("无法创建输出文件！")

if __name__ == "__main__":
    app = MySQLAddSchemaApp()
    app.mainloop()