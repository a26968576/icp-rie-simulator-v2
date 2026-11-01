"""Export: profile points CSV (um), PNG figure. Every output carries the model provenance label."""
from __future__ import annotations
import csv
import datetime as _dt
import json
from ..core import labels


def metadata(result, project=None):
    md = {"generator": "ICP-RIE Simulator V2", "model_label": result.label,
          "model_label_text": labels.TEXT[result.label],
          "calibrated": labels.is_calibrated(result.label), "length_unit": "um",
          "created": _dt.datetime.now().isoformat(timespec="seconds")}
    for k, v in result.meta.items():
        if isinstance(v, (str, int, float, bool)):
            if k.endswith("_nm") and isinstance(v, (int, float)) and not isinstance(v, bool):
                md[k[:-3] + "_um"] = v / 1000.0
            else:
                md[k] = v
    if project is not None:
        md["project"] = project.name
        if project.coefficients.calibration_note:
            md["calibration_note"] = project.coefficients.calibration_note
    return md


def export_profile_csv(result, path, frame_index=-1, project=None):
    fr = result.frames[frame_index]
    with open(path, "w", newline="", encoding="utf-8") as f:
        for k, v in metadata(result, project).items():
            f.write(f"# {k}: {v}\n")
        depth_um = {k: round(v / 1000.0, 4) for k, v in fr.depth_nm.items()}
        f.write(f"# time_s: {fr.time_s}\n# depth_um_per_opening: {json.dumps(depth_um)}\n")
        w = csv.writer(f)
        w.writerow(["segment", "x_um", "y_um"])
        for si, seg in enumerate(fr.surface):
            for x, y in seg:
                w.writerow([si, f"{x / 1000.0:.5f}", f"{y / 1000.0:.5f}"])


def export_png(figure, path, result, project=None):
    md = {k: str(v) for k, v in metadata(result, project).items()}
    figure.savefig(path, dpi=150, metadata={"Title": "ICP-RIE Simulator V2", "Description": json.dumps(md)})
