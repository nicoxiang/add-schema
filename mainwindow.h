#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QPushButton>
#include <QVBoxLayout>
#include <QList>
#include <QCheckBox>
#include <QMessageBox>

class MainWindow : public QMainWindow {
    Q_OBJECT
    
public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() = default;

private slots:
    void selectFile();
    void generateSql();

private:
    void loadSchemas();
    QString addSchemaToSql(const QString &sql, const QString &schema);
    void showWarning(const QString &message);
    QPushButton *fileBtn;
    QVBoxLayout *schemaLayout;
    QString selectedFile;
    QList<QCheckBox*> schemaCheckboxes;
};

#endif // MAINWINDOW_H