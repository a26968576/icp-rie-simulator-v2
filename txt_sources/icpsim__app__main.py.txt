"""Entry point:  python -m icpsim.app.main   (or: python run_app.py)"""
import sys


def main(argv=None):
    from PySide6.QtWidgets import QApplication
    from ..gui.main_window import MainWindow
    from PySide6.QtGui import QFont
    from .. import i18n
    args = sys.argv if argv is None else argv
    if "--en" in args:
        i18n.set_language("en")
    app = QApplication.instance() or QApplication(args)
    f = QFont("Microsoft JhengHei UI")
    f.setPointSize(10)
    app.setFont(f)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
