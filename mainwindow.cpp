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
    
    QStringList sqlStatements = sqlContent.split(';', Qt::SkipEmptyParts);
    
    QString outputFileName = selectedFile;
    outputFileName.replace(".sql", "_generated.sql");
    QFile outputFile(outputFileName);
    
    if (!outputFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        showWarning("无法创建输出文件！");
        return;
    }
    
    QTextStream out(&outputFile);
    for (const QString &schema : selectedSchemas) {
        for (QString stmt : sqlStatements) {
            stmt = stmt.trimmed();
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
