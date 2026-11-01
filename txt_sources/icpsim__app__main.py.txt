"""Entry point:  python -m icpsim.app.main   (or: python run_app.py)"""
import sys


def main(argv=None):
    from PySide6.QtWidgets import QApplication
    from ..gui.main_window import MainWindow
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
