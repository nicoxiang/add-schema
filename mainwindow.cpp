#include "mainwindow.h"
#include <QFileDialog>
#include <QScrollArea>
#include <QFile>
#include <QTextStream>
#include <QStandardPaths>
#include <QDir>
#include <QRegularExpression>

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    setWindowTitle("MySQL Add Schema工具");
    setGeometry(100, 100, 800, 600);
    
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    QVBoxLayout *layout = new QVBoxLayout(centralWidget);
    
    QFont buttonFont;
    buttonFont.setPointSize(12);

    fileBtn = new QPushButton("选择SQL文件", this);
    fileBtn->setFont(buttonFont);
    fileBtn->setMinimumHeight(50);
    fileBtn->setStyleSheet("QPushButton { padding: 10px; }");
    connect(fileBtn, &QPushButton::clicked, this, &MainWindow::selectFile);
    layout->addWidget(fileBtn);
    
    QScrollArea *scroll = new QScrollArea;
    QWidget *scrollWidget = new QWidget;
    schemaLayout = new QVBoxLayout(scrollWidget);
    scroll->setWidget(scrollWidget);
    scroll->setWidgetResizable(true);
    layout->addWidget(scroll);
    
    QPushButton *confirmBtn = new QPushButton("生成SQL", this);
    confirmBtn->setFont(buttonFont);
    confirmBtn->setMinimumHeight(50);
    confirmBtn->setStyleSheet("QPushButton { padding: 10px; background-color: #4CAF50; color: black; }");
    connect(confirmBtn, &QPushButton::clicked, this, &MainWindow::generateSql);
    layout->addWidget(confirmBtn);
    
    loadSchemas();
}

void MainWindow::showWarning(const QString &message) {
    QMessageBox::warning(this, "警告", message);
}

void MainWindow::selectFile() {
    QString fileName = QFileDialog::getOpenFileName(this,
        tr("选择SQL文件"),
        QString(),
        tr("SQL files (*.sql);;All Files (*)"));
        
    if (!fileName.isEmpty()) {
        selectedFile = fileName;
        fileBtn->setText("已选择: " + QFileInfo(fileName).fileName());
    }
}

QString MainWindow::addSchemaToSql(const QString &sql, const QString &schema) {
    QString modifiedSql = sql;
    
    // 匹配表名的正则表达式模式
    QStringList patterns = {
        // 修改UPDATE匹配模式，排除ON UPDATE CURRENT_TIMESTAMP的情况
        R"((?i)(?<!ON\s)UPDATE\s+(`?\w+`?))",  // UPDATE table，但不匹配ON UPDATE
        R"((?i)(FROM|JOIN|INTO)\s+(`?\w+`?))",  // FROM table, JOIN table, INTO table
        R"((?i)(CREATE|ALTER|DROP)\s+(TABLE|VIEW|TRIGGER|PROCEDURE|FUNCTION)\s+(`?\w+`?))", // DDL语句
        R"((?i)(INSERT\s+INTO)\s+(`?\w+`?))"  // INSERT INTO table
    };
    
    for (const QString &pattern : patterns) {
        QRegularExpression regex(pattern);
        QRegularExpressionMatchIterator i = regex.globalMatch(modifiedSql);
        
        while (i.hasNext()) {
            QRegularExpressionMatch match = i.next();
            QString tableName;
            if (pattern.contains("CREATE|ALTER|DROP")) {
                tableName = match.captured(3);
                // 保留关键字(TABLE等)
                QString keyword = match.captured(2);
                QString replacement = match.captured(1) + " " + keyword + " " + schema + "." + tableName;
                modifiedSql.replace(match.captured(0), replacement);
            } else if (pattern.contains("UPDATE") && !pattern.contains("ON UPDATE")) {
                // 处理UPDATE语句
                tableName = match.captured(1);
                if (!tableName.contains(".")) {
                    QString replacement = "UPDATE " + schema + "." + tableName;
                    modifiedSql.replace(match.captured(0), replacement);
                }
            } else {
                tableName = match.captured(2);
                // 如果表名没有schema前缀，添加schema
                if (!tableName.contains(".")) {
                    QString replacement = match.captured(1) + " " + schema + "." + tableName;
                    modifiedSql.replace(match.captured(0), replacement);
                }
            }
        }
    }
    
    return modifiedSql;
}

void MainWindow::generateSql() {
    // 检查是否选择了SQL文件
    if (selectedFile.isEmpty()) {
        showWarning("请先选择SQL文件！");
        return;
    }
    
    // 检查是否选择了至少一个schema
    QStringList selectedSchemas;
    for (QCheckBox *checkbox : schemaCheckboxes) {
        if (checkbox->isChecked()) {
            selectedSchemas.append(checkbox->text());
        }
    }
    
    if (selectedSchemas.isEmpty()) {
        showWarning("请至少选择一个Schema！");
        return;
    }
    
    QFile inputFile(selectedFile);
    if (!inputFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        showWarning("无法打开SQL文件！");
        return;
    }
    
    QString sqlContent = QTextStream(&inputFile).readAll();
    inputFile.close();
    
    // 修改SQL语句分割逻辑
    // 示例SQL:
    // CREATE TABLE test (id INT, name VARCHAR(50), COMMENT '这是一个;测试表');
    // INSERT INTO test VALUES (1, 'John;Smith');
    // UPDATE test SET name="Jane;Doe" WHERE id=1;
    QStringList sqlStatements;
    QString currentStatement;
    bool inSingleQuote = false;  // 跟踪是否在单引号内,例如: 'abc;def'
    bool inDoubleQuote = false;  // 跟踪是否在双引号内,例如: "xyz;123"
    bool inComment = false;      // 跟踪是否在注释内,例如: -- 这是一个注释;
    
    for(int i = 0; i < sqlContent.length(); i++) {
        QChar currentChar = sqlContent[i];
        QChar nextChar = (i + 1 < sqlContent.length()) ? sqlContent[i + 1] : QChar();
        
        // 处理引号 - 需要考虑转义字符
        if(currentChar == '\'' && !inDoubleQuote && !inComment) {
            if(i > 0 && sqlContent[i-1] == '\\') {
                // 处理转义的引号,例如: 'It\'s a test'
                currentStatement += currentChar;
                continue;
            }
            inSingleQuote = !inSingleQuote;
        } else if(currentChar == '"' && !inSingleQuote && !inComment) {
            if(i > 0 && sqlContent[i-1] == '\\') {
                // 处理转义的引号,例如: "Say \"Hello\""
                currentStatement += currentChar;
                continue;
            }
            inDoubleQuote = !inDoubleQuote;
        }
        
        // 处理注释 - 仅处理单行注释
        if(!inSingleQuote && !inDoubleQuote) {
            if(currentChar == '-' && nextChar == '-') {
                inComment = true;
            } else if(inComment && currentChar == '\n') {
                inComment = false;
            }
        }
        
        currentStatement += currentChar;
        
        // 只在非引号和非注释状态下检查分号
        // 例如: SELECT * FROM table WHERE col='abc;def'; -- 这里的分号才是语句结束
        if(!inSingleQuote && !inDoubleQuote && !inComment && currentChar == ';') {
            // 检查是否在COMMENT子句中
            // 例如: CREATE TABLE test (id INT, COMMENT '这里有;分号');
            QString upperStmt = currentStatement.toUpper();
            int commentPos = upperStmt.lastIndexOf("COMMENT");
            if(commentPos != -1) {
                // 从COMMENT开始向后查找匹配的引号对
                int quoteCount = 0;
                bool foundEndQuote = false;
                char quoteType = '\0';
                
                for(int j = commentPos; j < currentStatement.length(); j++) {
                    QChar ch = currentStatement[j];
                    if((ch == '\'' || ch == '"') && (j == 0 || currentStatement[j-1] != '\\')) {
                        if(quoteType == '\0') {
                            quoteType = ch.toLatin1();
                            quoteCount++;
                        } else if(ch.toLatin1() == quoteType) {
                            quoteCount++;
                            if(quoteCount == 2) {
                                foundEndQuote = true;
                                // 如果找到结束引号且当前位置后面有分号，则这是真正的语句结束
                                if(j < currentStatement.length() - 1 && currentStatement.indexOf(';', j) != -1) {
                                    sqlStatements.append(currentStatement.trimmed().chopped(1)); // 移除末尾分号
                                    currentStatement.clear();
                                }
                                break;
                            }
                        }
                    }
                }
                if(!foundEndQuote) {
                    // 如果没有找到结束引号，继续累积语句
                    continue;
                }
            } else {
                // 不在COMMENT子句中，正常分割
                sqlStatements.append(currentStatement.trimmed().chopped(1)); // 移除末尾分号
                currentStatement.clear();
            }
        }
    }
    
    // 处理最后一个语句（如果没有以分号结尾）
    // 例如文件末尾的: SELECT * FROM table
    if(!currentStatement.trimmed().isEmpty()) {
        sqlStatements.append(currentStatement.trimmed());
    }
    
    QString outputFileName = selectedFile;
    outputFileName.replace(".sql", "_generated.sql");
    QFile outputFile(outputFileName);
    
    if (!outputFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        showWarning("无法创建输出文件！");
        return;
    }
    
    QTextStream out(&outputFile);
    for (const QString &schema : selectedSchemas) {
        for (const QString &stmt : sqlStatements) {
            if (!stmt.isEmpty()) {
                out << addSchemaToSql(stmt, schema) << ";\n\n";
            }
        }
    }
    
    outputFile.close();
    QMessageBox::information(this, "成功", "文件生成成功！");
}

void MainWindow::loadSchemas() {
    QString configPath = QDir::home().filePath("schemas.conf");
    QFile file(configPath);
    
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QTextStream in(&file);
        while (!in.atEnd()) {
            QString schema = in.readLine().trimmed();
            if (!schema.isEmpty()) {
                QCheckBox *checkbox = new QCheckBox(schema);
                schemaCheckboxes.append(checkbox);
                schemaLayout->addWidget(checkbox);
            }
        }
        file.close();
    }
}
