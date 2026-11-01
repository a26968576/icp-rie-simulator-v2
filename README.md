# ICP-RIE Simulator V2

Windows 2D etch-profile simulator (Python + PySide6 + Matplotlib, optional ViennaPS).
First validation case: **GaN etched in Cl2/BCl3 ICP-RIE** with SiO2 or photoresist mask.

## RESULT PROVENANCE - READ FIRST
Every result is labelled (GUI banner, plot title/watermark, CSV header, PNG metadata, project JSON):

| Label | Meaning |
|---|---|
| `DEMO` | Empirical cell model with **uncalibrated, illustrative** coefficients. NOT physical truth. |
| `CALIBRATED` | Demo profile model with rate scale (and optionally ARDE alpha) fitted to *your* depth-vs-time data. Valid only near the calibrated recipe. |
| `VIENNAPS_UNCALIBRATED` | Real ViennaPS level-set surface evolution (DirectionalProcess), but rates are still demo coefficients. |
| `VIENNAPS_CALIBRATED` | ViennaPS geometry + calibrated rates. |

Even "calibrated" does not mean a predictive plasma model: the gas-chemistry trends
(`core/gas_chemistry.py`) are simple proxies, not a plasma simulation.

## Units
All user-facing lengths are **micrometers** (GUI, plots, CSV `x_um,y_um`, JSON v3 `*_um`); rates in um/min.
Internals are nm. Old v2 JSON (nm) still loads.

## GUI
Left *Process* tab top->bottom: (1) Mask & materials, (2) Gas species & flows, (3) Main recipe, then the green
**RUN SIMULATION** button. *Advanced* tab: backend, ARDE/loading, calibration, material library.
Icon toolbar: presets, open/save, run/stop/reset, before/after toggle, export PNG/CSV/JSON; timeline play/pause.

## Layout
```
run_app.py                 launcher / PyInstaller entry
make_screenshot.py         headless GUI screenshot
icpsim/app/main.py         QApplication entry
icpsim/gui/                main_window, style (QSS), icons (painted), recipe_panel (+GasFlowPanel), material_editor (materials+layers),
                           mask_editor (mask/CD/selectivity), settings_panel, calibration_panel,
                           timeline (slider), profile_view (before/after canvas), widgets
icpsim/core/               materials, layer_stack, mask, recipe (+rates), gas_chemistry, project (+GaN preset),
                           frames (results), labels (provenance)
icpsim/models/             demo_model.py (cell model, ion directional + chemical isotropic),
                           physics_backend_viennaps.py (real ViennaPS adapter + fallback)
icpsim/extensions/         loading.py, arde.py
icpsim/calibration/fit.py  fit from CSV time_s,depth_um[,cd_um] (or _nm)
icpsim/io/                 project_io.py (JSON), export.py (PNG, CSV)
tests/                     pytest (core, demo model, viennaps/fallback, calibration, io, GUI smoke)
examples/                  example calibration CSV
```

## Run
Windows, no typing: double-click `install.bat` once (creates `.venv`, installs requirements, tries optional ViennaPS;
put a proxy URL in `proxy.txt` if your network needs one), then double-click `run.bat`.

Manual:
```
pip install -r requirements.txt
python run_app.py            # or: python -m icpsim.app.main
set QT_QPA_PLATFORM=offscreen && python -m pytest -q
```

## Rate sources, literature DB, selectivity (V2.1)
- UI is Traditional Chinese with English in parentheses; toolbar `English` toggles, or start with `python -m app.main --en`.
- Gases CF4, O2, Ar, BCl3, Cl2, N2 with quick-add buttons.
- Add materials (e.g. 光阻1, PDMS) without physical factors. Per chemistry, give either an absolute experimental rate
  (Å/s, nm/min, µm/min) or a selectivity `S = R_target / R_mask` vs a reference (30 Å/s resist, 100 Å/s PDMS → 3.33).
- Priority: user experimental > literature (median of enabled entries matching the recipe's gas set) > demo factors.
  Chains are propagated, cycles checked for consistency, missing data warned. Selectivity matrix view; library JSON save/load.
- Literature DB (`icpsim/data/literature_db.json`, 44 entries / 13 sources, all cited with conditions) is editable in
  the Advanced tab; edits saved to `~/.icp_rie_sim/literature_db.json`.
- Labels: EXPERIMENTAL_INPUT / LITERATURE_BASED (and VIENNAPS_* variants) in addition to DEMO / CALIBRATED.
- Limitations: experimental/literature rates are fixed and do not scale with power/pressure; profile shape is still the
  demo model; no SEM overlay or parameter sweep.
