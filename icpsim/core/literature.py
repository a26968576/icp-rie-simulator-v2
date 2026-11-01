"""Literature etch-rate / selectivity database (icpsim/data/literature_db.json).

Every entry was transcribed from a cited publication (authors, title, year, DOI/URL)
together with the recipe conditions. Nothing is invented. Tools and conditions
differ from yours: literature values are a rough guide, flagged as LITERATURE.
selectivity = target etch rate / mask etch rate.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "literature_db.json"
USER_DB_PATH = Path(os.path.expanduser("~")) / ".icp_rie_sim" / "literature_db.json"
FORMAT = "icp-rie-sim-v2/literature-db"
REQUIRED_SOURCE = ("authors", "title", "year")

# app material name aliases -> literature names
ALIASES = {"SiN": "Si3N4", "PR": "Photoresist", "AZ": "Photoresist", "SPR": "Photoresist",
           "Al2O3": "Sapphire", "PI": "Polyimide", "SU8": "SU-8"}


def canon(name: str) -> str:
    return ALIASES.get(name, name)


def is_ic_plasma(entry) -> bool:
    return str(entry.get("tool", "")).upper().startswith("ICP")


def validate_entry(e) -> list:
    """Return list of problems (empty = ok)."""
    errs = []
    src = e.get("source") or {}
    for k in ("authors", "title"):
        if not str(src.get(k, "")).strip():
            errs.append(f"{e.get('id')}: source.{k} missing")
    if "year" not in src:
        errs.append(f"{e.get('id')}: source.year missing")
    if not (str(src.get("doi", "")).strip() or str(src.get("url", "")).strip()):
        errs.append(f"{e.get('id')}: DOI or URL required")
    if not e.get("gases"):
        errs.append(f"{e.get('id')}: gases missing")
    if e.get("kind") == "rate":
        if not e.get("material"):
            errs.append(f"{e.get('id')}: material missing")
        if e.get("rate_nm_min") is None and not e.get("rate_range_nm_min"):
            errs.append(f"{e.get('id')}: rate missing")
    elif e.get("kind") == "selectivity":
        if not e.get("target") or not e.get("mask"):
            errs.append(f"{e.get('id')}: target/mask missing")
        if e.get("selectivity") is None and not e.get("selectivity_range"):
            errs.append(f"{e.get('id')}: selectivity missing")
    else:
        errs.append(f"{e.get('id')}: kind must be rate|selectivity")
    return errs


def value_of(e):
    """Representative value. Ranges -> midpoint (flagged in `note`)."""
    if e["kind"] == "rate":
        v, r = e.get("rate_nm_min"), e.get("rate_range_nm_min")
    else:
        v, r = e.get("selectivity"), e.get("selectivity_range")
    if v is not None:
        return float(v)
    return 0.5 * (float(r[0]) + float(r[1]))


class LiteratureDB:
    def __init__(self, entries=None, note=""):
        self.entries = list(entries or [])
        self.note = note
        for e in self.entries:
            # by default only ICP-tool entries are used for rate resolution (RIE/asher only as reference)
            e.setdefault("enabled", is_ic_plasma(e))

    @staticmethod
    def load(path=None) -> "LiteratureDB":
        if path is None:
            path = USER_DB_PATH if USER_DB_PATH.exists() else DEFAULT_DB_PATH
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("format") != FORMAT:
            raise ValueError("Not a literature DB file")
        return LiteratureDB(d.get("entries", []), d.get("note", ""))

    def save(self, path=None):
        path = Path(path or USER_DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"format": FORMAT, "version": 1, "note": self.note, "entries": self.entries},
                      f, indent=1, ensure_ascii=False)
        return path

    def copy(self):
        return LiteratureDB(copy.deepcopy(self.entries), self.note)

    def problems(self):
        out = []
        for e in self.entries:
            out += validate_entry(e)
        return out

    def matching(self, gases_set, kind=None, enabled_only=True):
        gs = frozenset(gases_set)
        for e in self.entries:
            if enabled_only and not e.get("enabled", True):
                continue
            if kind and e.get("kind") != kind:
                continue
            if frozenset(e.get("gases", [])) == gs:
                yield e

    def materials(self):
        s = set()
        for e in self.entries:
            for k in ("material", "target", "mask"):
                if e.get(k):
                    s.add(e[k])
        return sorted(s)


def cite(e) -> str:
    s = e["source"]
    ref = s.get("doi") and f"doi:{s['doi']}" or s.get("url", "")
    return f"{s['authors']} ({s.get('year') or 'n.d.'}) {s['title']}. {s.get('journal', '')} {ref}".strip()


_ACTIVE = None


def get_active() -> LiteratureDB:
    global _ACTIVE
    if _ACTIVE is None:
        try:
            _ACTIVE = LiteratureDB.load()
        except Exception:  # noqa: BLE001  corrupt user copy -> fall back to shipped DB
            _ACTIVE = LiteratureDB.load(DEFAULT_DB_PATH)
    return _ACTIVE


def set_active(db: LiteratureDB):
    global _ACTIVE
    _ACTIVE = db
