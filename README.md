# 本项目所有内容均由cursor生成

# Add Schema 工具

这是一个用于为MySQL SQL语句批量添加schema的工具。

## 功能特点

- 支持选择SQL文件并读取其中的SQL语句
- 从用户主目录下的配置文件读取可用的schema列表
- 支持多选schema
- 自动为SQL语句添加选定的schema前缀
- 支持DDL和DML语句
- 生成新的SQL文件，保留原文件不变

## 配置文件

在用户主目录下创建`schemas.conf`文件，每行写入一个schema名称