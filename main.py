import sys
from MainWindow_logic import MainWindow_logic
from PySide6.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow_logic()
    mw.show()
    app.exec()