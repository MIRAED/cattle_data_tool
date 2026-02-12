import sys
from PySide6.QtWidgets import (QApplication)

from main_window import CowAnalyzer


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CowAnalyzer()
    window.show()
    sys.exit(app.exec())