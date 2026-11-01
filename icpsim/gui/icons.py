"""Programmatically painted icons (no external image files needed)."""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygonF, QFont, QPen

GREEN, RED, BLUE, GREY, ORANGE, PURPLE = "#2e9d46", "#d32f2f", "#1e6fd9", "#546e7a", "#ef6c00", "#7b1fa2"


def _canvas(size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def play(color=GREEN, size=64):
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    s = size
    p.drawPolygon(QPolygonF([QPointF(s * .22, s * .12), QPointF(s * .88, s * .5), QPointF(s * .22, s * .88)]))
    p.end()
    return QIcon(pm)


def pause(color=BLUE, size=64):
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(size * .2, size * .14, size * .2, size * .72), 4, 4)
    p.drawRoundedRect(QRectF(size * .6, size * .14, size * .2, size * .72), 4, 4)
    p.end()
    return QIcon(pm)


def stop(color=RED, size=64):
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(size * .18, size * .18, size * .64, size * .64), 8, 8)
    p.end()
    return QIcon(pm)


def reset(color=ORANGE, size=64):
    pm, p = _canvas(size)
    pen = QPen(QColor(color), size * .11); pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    r = QRectF(size * .18, size * .18, size * .64, size * .64)
    p.drawArc(r, 60 * 16, 290 * 16)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(size * .55, size * .02), QPointF(size * .82, size * .2),
                             QPointF(size * .52, size * .36)]))
    p.end()
    return QIcon(pm)


def badge(text, color=BLUE, size=64):
    """Rounded colored tile with a short label, e.g. PNG / CSV / JSON."""
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(2, size * .14, size - 4, size * .72), 10, 10)
    f = QFont(); f.setBold(True); f.setPixelSize(int(size * (0.34 if len(text) <= 3 else 0.27)))
    p.setFont(f); p.setPen(QColor("white"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, text)
    p.end()
    return QIcon(pm)


def folder(color="#f9a825", size=64):
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(size * .06, size * .2, size * .4, size * .2), 5, 5)
    p.drawRoundedRect(QRectF(size * .06, size * .3, size * .88, size * .52), 6, 6)
    p.end()
    return QIcon(pm)


def disk(color=BLUE, size=64):
    pm, p = _canvas(size)
    p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(size * .1, size * .1, size * .8, size * .8), 8, 8)
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(size * .26, size * .14, size * .48, size * .26))
    p.drawRoundedRect(QRectF(size * .24, size * .56, size * .52, size * .3), 3, 3)
    p.end()
    return QIcon(pm)


def compare(size=64):
    """Before/after split icon."""
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(GREY)); p.drawRoundedRect(QRectF(size * .06, size * .16, size * .42, size * .68), 6, 6)
    p.setBrush(QColor(BLUE)); p.drawRoundedRect(QRectF(size * .52, size * .16, size * .42, size * .68), 6, 6)
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(size * .64, size * .16, size * .18, size * .34))
    p.end()
    return QIcon(pm)


def wafer(size=64):
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#d9c27a")); p.drawRect(QRectF(size * .08, size * .66, size * .84, size * .18))
    p.setBrush(QColor("#4f7fbf")); p.drawRect(QRectF(size * .08, size * .36, size * .84, size * .3))
    p.setBrush(QColor("#9e9e9e"))
    p.drawRect(QRectF(size * .08, size * .22, size * .26, size * .14))
    p.drawRect(QRectF(size * .66, size * .22, size * .26, size * .14))
    p.setBrush(QColor("white")); p.drawRect(QRectF(size * .34, size * .36, size * .32, size * .16))
    p.end()
    return QIcon(pm)
