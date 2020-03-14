from SnailPDF import ui
from PySide2.QtCore import Qt
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QtWidgets.QApplication()
    window = ui.MainWindow()
    window.resize(1000, 600)
    window.show()
    app.exec_()