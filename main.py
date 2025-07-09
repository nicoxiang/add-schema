import os
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sqlglot.errors import *

from sql_exceptions import UnsupportedSQLError
from sql_utils import (
    split_sql_statements,
    add_schema_to_sql,
)

class MySQLAddSchemaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MySQL Add Schema工具")
        self.geometry("800x700")
        self.selected_file = ""
        self.selected_schemas = []
        self.schema_vars = []
        self.schemas = []
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

        # 绑定鼠标滚轮事件到canvas
        self._bind_mousewheel(self.schema_canvas)

        # 全选勾选框变量
        self.select_all_var = tk.BooleanVar()
        # 全选勾选框（放在schema_inner的最上方，与其他勾选框y轴对齐）
        self.select_all_cb = tk.Checkbutton(
            self.schema_inner, text="全选", variable=self.select_all_var, anchor="w",
            command=self.toggle_select_all
        )
        self.select_all_cb.pack(fill=tk.X, padx=5, pady=2, anchor="w")

        # 生成按钮
        self.confirm_btn = tk.Button(self, text="生成SQL", font=("Arial", 12), height=2, bg="#4CAF50", fg="black",
                                     command=self.generate_sql)
        self.confirm_btn.pack(fill=tk.X, padx=10, pady=10)
        self.load_schemas()

    def _bind_mousewheel(self, widget):
        # 只在内容超出时绑定鼠标滚轮
        widget.bind("<Enter>", self._maybe_bind_mousewheel)
        widget.bind("<Leave>", self._maybe_unbind_mousewheel)

    def _maybe_bind_mousewheel(self, event):
        # 判断内容是否超出可视区域，超出才绑定
        canvas = event.widget
        if not isinstance(canvas, tk.Canvas):
            return
        bbox = canvas.bbox("all")
        if bbox is None:
            return
        content_height = bbox[3] - bbox[1]
        visible_height = canvas.winfo_height()
        if content_height > visible_height:
            # 绑定滚轮
            canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux
            canvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux
        else:
            # 解绑滚轮
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

    def _maybe_unbind_mousewheel(self, event):
        canvas = event.widget
        if not isinstance(canvas, tk.Canvas):
            return
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # 只在内容超出时允许滚动
        bbox = self.schema_canvas.bbox("all")
        if bbox is None:
            return
        content_height = bbox[3] - bbox[1]
        visible_height = self.schema_canvas.winfo_height()
        if content_height <= visible_height:
            return  # 不允许滚动
        if event.num == 4:  # Linux scroll up
            self.schema_canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.schema_canvas.yview_scroll(1, "units")
        else:
            delta = event.delta
            if delta == 0:
                return
            if os.name == "nt":
                self.schema_canvas.yview_scroll(-1 * int(delta / 120), "units")
            else:
                self.schema_canvas.yview_scroll(-1 * int(delta), "units")

    @staticmethod
    def show_warning(message):
        messagebox.showwarning("警告", message)

    def toggle_select_all(self):
        # 设置所有schema勾选框的值为全选框的值
        value = self.select_all_var.get()
        for var in self.schema_vars:
            var.set(value)

    def update_select_all(self, *args):
        # 如果所有schema勾选框都被选中，则全选框也选中，否则不选中
        if self.schema_vars:
            all_selected = all(var.get() for var in self.schema_vars)
            self.select_all_var.set(all_selected)
        else:
            self.select_all_var.set(False)

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
                        # 绑定每个schema勾选框的变化到update_select_all
                        var.trace_add("write", self.update_select_all)
                        cb = tk.Checkbutton(self.schema_inner, text=schema, variable=var, anchor="w")
                        cb.pack(fill=tk.X, padx=5, pady=2, anchor="w")
                        self.schema_vars.append(var)
                        self.schemas.append(schema)

    def generate_sql(self):
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
        except PermissionError:
            self.show_warning("读取源SQL文件权限不足！")
            return
        except OSError:
            self.show_warning("无法打开源SQL文件！")
            return

        try:
            sql_statements = split_sql_statements(sql_content)

            p = pathlib.Path(self.selected_file)
            output_file_name = str(p.with_name(p.stem + '_generated.sql'))

            with open(output_file_name, "w", encoding="utf-8") as out:
                for schema in selected_schemas:
                    for statement in sql_statements:
                        if statement.strip():
                            new_sql = add_schema_to_sql(statement, schema)
                            out.write(new_sql.strip() + ";\n\n")
            messagebox.showinfo("成功", "文件生成成功！\n输出文件: " + output_file_name)
        except (ParseError, TokenError, OptimizeError):
            self.show_warning("源SQL文件解析失败！")
        except UnsupportedSQLError:
            self.show_warning("存在无法解析的SQL！")
        except PermissionError:
            self.show_warning("写入目标SQL文件权限不足！")
        except OSError:
            self.show_warning("写入目标SQL文件失败！")

if __name__ == "__main__":
    app = MySQLAddSchemaApp()
    app.mainloop()