"""Etch-rate source resolution per material and recipe chemistry.

Priority (highest first):
  1. user EXPERIMENTAL data (absolute rate, or selectivity chained to a known rate);
     a CALIBRATED GaN model counts as experimental
  2. LITERATURE database (absolute rate, or literature selectivity chained to a known rate)
  3. mask-tab selectivity preset (mask only) / DEMO physical factors
  4. none -> warning, material is treated as not etched

Selectivity definition (user's convention):
    S = R_target / R_mask      e.g. resist 30 A/s, PDMS 100 A/s  ->  S(PDMS:resist) = 100/30 = 3.33
"""
from __future__ import annotations
import math
from dataclasses import dataclass, asdict, field
from .literature import LiteratureDB, canon, value_of, cite

UNITS = {"A/s": 6.0, "nm/min": 1.0, "um/min": 1000.0, "nm/s": 60.0}   # -> nm/min
SEL_FORMULA = "選擇比 S = R_目標 / R_光罩  (Selectivity = target rate / mask rate)"

EXPERIMENTAL, CALIBRATED, LITERATURE, PRESET, DEMO, NONE = (
    "experimental", "calibrated", "literature", "preset", "demo", "none")


def to_nm_min(value: float, unit: str) -> float:
    return float(value) * UNITS[unit]


def from_nm_min(v: float, unit: str) -> float:
    return float(v) / UNITS[unit]


def selectivity(target_rate: float, mask_rate: float) -> float:
    if mask_rate <= 0:
        return math.inf
    return target_rate / mask_rate


def chem_key(gases) -> frozenset:
    if isinstance(gases, dict):
        return frozenset(k for k, v in gases.items() if v and v > 0)
    return frozenset(gases)


def parse_chem(text: str):
    t = (text or "*").strip()
    if t in ("*", "", "any", "全部"):
        return None
    return frozenset(x.strip() for x in t.replace("+", "/").replace(",", "/").split("/") if x.strip())


def chem_text(key) -> str:
    return "/".join(sorted(key)) if key else "*"


@dataclass
class UserRateEntry:
    """kind='rate': `material` etches at value [unit].
    kind='selectivity': S = R(material) / R(reference) = value."""
    material: str
    kind: str = "rate"
    value: float = 0.0
    unit: str = "A/s"
    reference: str = ""
    chemistry: str = "*"          # e.g. "Cl2/BCl3" ; "*" = any recipe
    note: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return UserRateEntry(**{k: v for k, v in d.items() if k in UserRateEntry.__dataclass_fields__})

    def matches(self, key) -> bool:
        c = parse_chem(self.chemistry)
        return c is None or c == key


@dataclass
class Resolved:
    material: str
    rate_nm_min: float | None
    source: str
    detail: str = ""

    @property
    def rate_A_s(self):
        return None if self.rate_nm_min is None else self.rate_nm_min / 6.0


@dataclass
class Resolution:
    rates: dict = field(default_factory=dict)        # name -> Resolved
    warnings: list = field(default_factory=list)
    cycles: list = field(default_factory=list)
    chemistry: frozenset = frozenset()

    def provenance(self, names):
        return {n: self.rates[n].source for n in names if n in self.rates}


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def find_cycles(edges):
    """edges: list of (a, b, S, origin). Returns list of (cycle node list, consistent bool).
    Uses union-find with log-potential: a second path between connected nodes = cycle."""
    parent, pot = {}, {}   # pot[x] = log R(x) - log R(root)

    def find(x):
        parent.setdefault(x, x); pot.setdefault(x, 0.0)
        if parent[x] == x:
            return x
        par = parent[x]
        r = find(par)
        if par != r:
            pot[x] += pot[par]
        parent[x] = r
        return r

    adj = {}
    cycles = []
    for a, b, s, origin in edges:
        if s is None or s <= 0:
            continue
        ra, rb = find(a), find(b)
        pa, pb = pot[a], pot[b]
        want = math.log(s)              # log R(a) - log R(b)
        if ra == rb:
            got = pa - pb
            path = _path(adj, a, b) or [a, b]
            cycles.append((path + [a], abs(got - want) < math.log(1.05)))
        else:
            parent[ra] = rb
            pot[ra] = want + pb - pa
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    return cycles


def _path(adj, a, b):
    prev, q = {a: None}, [a]
    while q:
        x = q.pop(0)
        if x == b:
            out = [b]
            while prev[out[-1]] is not None:
                out.append(prev[out[-1]])
            return out[::-1]
        for y in adj.get(x, ()):
            if y not in prev:
                prev[y] = x; q.append(y)
    return None


def resolve(materials, gases, user_entries=(), literature: LiteratureDB | None = None,
            demo_rates_nm_min=None, calibrated=None, mask_material=None, mask_target=None,
            mask_selectivity=None):
    """Resolve an etch rate (nm/min, total of ion+chemical) for each material name.

    demo_rates_nm_min : {name: rate} from the DEMO physical-factor model (materials with factors)
    calibrated        : {name: rate} from a calibrated model (counts as experimental)
    mask_* : mask-tab selectivity preset, fallback for the mask only
    """
    key = chem_key(gases)
    res = Resolution(chemistry=key)
    names = list(materials)
    R = res.rates
    ue = [u for u in user_entries if u.matches(key)]
    u_edges = [(u.material, u.reference, float(u.value), "experimental")
               for u in ue if u.kind == "selectivity" and u.reference]
    l_edges, l_sel_src = [], {}
    lit_abs = {}
    if literature is not None:
        for e in literature.matching(key, "rate"):
            lit_abs.setdefault(e["material"], []).append(e)
        groups = {}
        for e in literature.matching(key, "selectivity"):
            groups.setdefault((e["target"], e["mask"]), []).append(e)
        for (t, m), es in groups.items():
            s = _median([value_of(e) for e in es])
            l_edges.append((t, m, s, "literature"))
            l_sel_src[(t, m)] = es

    def lname(n):          # literature uses canonical names
        return canon(n)

    # map literature names onto app materials
    lit_to_app = {}
    for n in names:
        lit_to_app.setdefault(lname(n), n)
    l_edges = [(lit_to_app[a], lit_to_app[b], s, o) for a, b, s, o in l_edges
               if a in lit_to_app and b in lit_to_app]

    # cycle detection on all selectivity data for this chemistry
    for cyc, ok in find_cycles(u_edges + l_edges):
        res.cycles.append((cyc, ok))
        txt = " → ".join(cyc)
        if ok:
            res.warnings.append(f"選擇比循環 (selectivity cycle, consistent): {txt}")
        else:
            res.warnings.append(f"選擇比循環且數值矛盾 (INCONSISTENT selectivity cycle): {txt} — 使用最先解出的值")

    def propagate(edges, src, tag):
        changed = True
        while changed:
            changed = False
            for a, b, s, _ in edges:
                if s <= 0:
                    continue
                if b in R and a not in R and R[b].rate_nm_min is not None:
                    R[a] = Resolved(a, R[b].rate_nm_min * s, src(R[b]),
                                    f"R({a}) = S × R({b}) = {s:.3g} × {R[b].rate_nm_min:.4g} nm/min [{tag}]")
                    changed = True
                elif a in R and b not in R and R[a].rate_nm_min is not None:
                    R[b] = Resolved(b, R[a].rate_nm_min / s, src(R[a]),
                                    f"R({b}) = R({a}) / S = {R[a].rate_nm_min:.4g} / {s:.3g} nm/min [{tag}]")
                    changed = True

    # 1. user absolute
    for u in ue:
        if u.kind == "rate" and u.material in names and u.material not in R:
            R[u.material] = Resolved(u.material, to_nm_min(u.value, u.unit), EXPERIMENTAL,
                                     f"使用者實驗值 (user experimental) {u.value:g} {u.unit}")
    for n, v in (calibrated or {}).items():
        if n in names and n not in R:
            R[n] = Resolved(n, v, CALIBRATED, "校正模型 (calibrated model)")
    propagate(u_edges, lambda r: EXPERIMENTAL if r.source in (EXPERIMENTAL, CALIBRATED) else r.source,
              "使用者選擇比 user selectivity")
    # 2. literature absolute
    for n in names:
        if n not in R and lname(n) in lit_abs:
            es = lit_abs[lname(n)]
            v = _median([value_of(e) for e in es])
            R[n] = Resolved(n, v, LITERATURE, f"文獻 (literature) median of {len(es)}: " +
                            "; ".join(e["id"] for e in es))
    # user selectivity anchored on literature: result is literature-based
    propagate(u_edges, lambda r: r.source, "使用者選擇比 user selectivity")
    propagate(l_edges, lambda r: LITERATURE if r.source != PRESET else PRESET, "文獻選擇比 literature selectivity")
    propagate(u_edges, lambda r: r.source, "使用者選擇比 user selectivity")
    # 3. demo
    for n in names:
        if n not in R and demo_rates_nm_min and demo_rates_nm_min.get(n) is not None and n != mask_material:
            R[n] = Resolved(n, demo_rates_nm_min[n], DEMO, "DEMO 物理因子 (demo factors)")
    propagate(u_edges, lambda r: r.source, "使用者選擇比 user selectivity")
    propagate(l_edges, lambda r: r.source, "文獻選擇比 literature selectivity")
    if mask_material and mask_material not in R and mask_target in R and mask_selectivity:
        R[mask_material] = Resolved(mask_material, R[mask_target].rate_nm_min / mask_selectivity, PRESET,
                                    f"光罩頁選擇比 (mask-tab selectivity) R = R({mask_target}) / {mask_selectivity:g}")
    for n in names:
        if n not in R and demo_rates_nm_min and demo_rates_nm_min.get(n) is not None:
            R[n] = Resolved(n, demo_rates_nm_min[n], DEMO, "DEMO 物理因子 (demo factors)")
    for n in names:
        if n not in R:
            R[n] = Resolved(n, None, NONE, "無資料 (no data)")
            res.warnings.append(f"{n}: 此氣體化學 ({chem_text(key)}) 無蝕刻率資料，視為不蝕刻 "
                                f"(no rate data — treated as NOT etched)")
    return res


def selectivity_matrix(resolution: Resolution, names):
    """M[i][j] = R(names[i]) / R(names[j])  (row = target, column = mask)."""
    M = []
    for a in names:
        row = []
        for b in names:
            ra = resolution.rates.get(a); rb = resolution.rates.get(b)
            if ra is None or rb is None or ra.rate_nm_min is None or rb.rate_nm_min is None:
                row.append(None)
            else:
                row.append(selectivity(ra.rate_nm_min, rb.rate_nm_min))
        M.append(row)
    return M


__all__ = ["UserRateEntry", "resolve", "selectivity", "selectivity_matrix", "to_nm_min", "from_nm_min",
           "SEL_FORMULA", "cite"]


_RANK = {NONE: 5, DEMO: 4, LITERATURE: 3, PRESET: 2, CALIBRATED: 1, EXPERIMENTAL: 0}


def merge_provenance(resolutions, names):
    """Worst (least trustworthy) source per material over all recipe steps."""
    out = {}
    for r in resolutions:
        for n, src in r.provenance(names).items():
            if n not in out or _RANK[src] > _RANK[out[n]]:
                out[n] = src
    return out


def rate_meta(resolutions, names):
    """JSON-friendly summary stored in SimResult.meta."""
    prov = merge_provenance(resolutions, names)
    warns = []
    for r in resolutions:
        for w in r.warnings:
            if w not in warns:
                warns.append(w)
    first = resolutions[0] if resolutions else None
    return {"rate_sources": prov,
            "rate_details": {n: {"rate_nm_min": first.rates[n].rate_nm_min, "source": first.rates[n].source,
                                 "detail": first.rates[n].detail} for n in names} if first else {},
            "rate_warnings": warns}
