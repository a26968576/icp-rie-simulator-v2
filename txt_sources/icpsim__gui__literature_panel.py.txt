"""Editable literature database table (Advanced tab)."""
from __future__ import annotations
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from ..core import literature as lit
from ..i18n import tr
from .widgets import make_table, set_rows, get_rows, add_remove_bar, note

COLS = ["hdr_on", "hdr_id", "hdr_kind", "hdr_target", "hdr_mask", "hdr_gases", "hdr_value", "hdr_tool",
        "hdr_authors", "hdr_title", "hdr_year", "hdr_doi", "hdr_cond"]


def _val_text(e):
    if e["kind"] == "rate":
        v, r, u = e.get("rate_nm_min"), e.get("rate_range_nm_min"), " nm/min"
    else:
        v, r, u = e.get("selectivity"), e.get("selectivity_range"), ""
    return (f"{v:g}" if v is not None else f"{r[0]:g}-{r[1]:g}") + u


def _parse_val(t):
    t = t.replace("nm/min", "").strip()
    if "-" in t[1:]:
        a, b = t.split("-", 1) if not t.startswith("-") else t[1:].split("-", 1)
        return None, [float(a), float(b)]
    return float(t), None


class LiteraturePanel(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        v.addWidget(note(tr("lit_note")))
        self.count = QLabel()
        v.addWidget(self.count)
        self.table = make_table([tr(k) for k in COLS], max_rows=10, stretch=False)
        v.addWidget(self.table)
        self.save_btn = QPushButton(tr("lit_save"))
        self.reload_btn = QPushButton(tr("lit_reload"))
        self.save_btn.clicked.connect(lambda: self.save())
        self.reload_btn.clicked.connect(self.restore_builtin)
        v.addWidget(add_remove_bar(self._add, self._remove, trailing=[self.save_btn, self.reload_btn]))
        self.status = QLabel()
        self.status.setWordWrap(True)
        v.addWidget(self.status)
        self.db = lit.get_active()
        self.show_db(self.db)

    def show_db(self, db):
        self.db = db
        rows = []
        for e in db.entries:
            s = e["source"]
            rows.append([1 if e.get("enabled", True) else 0, e["id"], e["kind"],
                         e.get("material") or e.get("target", ""), e.get("mask", ""), "/".join(e["gases"]),
                         _val_text(e), e.get("tool", ""), s.get("authors", ""), s.get("title", ""),
                         s.get("year") or "", s.get("doi") or s.get("url", ""),
                         json.dumps(e.get("conditions", {}), ensure_ascii=False)])
        set_rows(self.table, rows)
        self.count.setText(f"{len(db.entries)} entries / {len({e['source']['title'] for e in db.entries})} sources")

    def entries_from_table(self):
        old = {e["id"]: e for e in self.db.entries}
        out = []
        for r in get_rows(self.table):
            (on, eid, kind, mat, mask, gases, val, tool, authors, title, year, ref, cond) = r
            e = dict(old.get(eid, {"id": eid}))
            e["enabled"] = on.strip() in ("1", "true", "True", "yes")
            e["kind"] = "selectivity" if kind.strip().startswith("sel") else "rate"
            e["gases"] = [g.strip() for g in gases.split("/") if g.strip()]
            e["tool"] = tool
            v, rng = _parse_val(val)
            e.pop("material", None); e.pop("target", None)
            if e["kind"] == "rate":
                e["material"] = mat.strip(); e["rate_nm_min"] = v; e["rate_range_nm_min"] = rng
            else:
                e["target"] = mat.strip(); e["mask"] = mask.strip(); e["selectivity"] = v; e["selectivity_range"] = rng
            src = dict(e.get("source", {}))
            src.update(authors=authors, title=title, year=int(year) if year.strip().isdigit() else None)
            if ref.startswith("http"):
                src["url"] = ref
            else:
                src["doi"] = ref
            e["source"] = src
            try:
                e["conditions"] = json.loads(cond) if cond.strip() else {}
            except ValueError:
                e["conditions"] = {"text": cond}
            out.append(e)
        return out

    def apply(self):
        self.db = lit.LiteratureDB(self.entries_from_table(), self.db.note)
        lit.set_active(self.db)
        probs = self.db.problems()
        self.status.setText((tr("lit_problems") + " " + "; ".join(probs)) if probs else "")
        return self.db

    def save(self, path=None):
        db = self.apply()
        p = db.save(path)
        self.status.setText(self.status.text() + "  " + tr("lit_saved", p=str(p)))
        return p

    def restore_builtin(self):
        self.show_db(lit.LiteratureDB.load(lit.DEFAULT_DB_PATH))
        lit.set_active(self.db)

    def _add(self):
        db = lit.LiteratureDB(self.entries_from_table(), self.db.note)
        n = max([int(e["id"][1:]) for e in db.entries if e["id"][1:].isdigit()] + [0]) + 1
        db.entries.append({"id": f"U{n:03d}", "kind": "rate", "material": "", "gases": [], "rate_nm_min": 0.0,
                           "tool": "ICP", "conditions": {}, "enabled": False,
                           "source": {"authors": "", "title": "", "year": None, "doi": "", "url": ""}})
        self.show_db(db)

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
