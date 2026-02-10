"""Batch process CAG/PCI files with a file dialog and merge scores.

Workflow:
1) Select one or more CSV/XLSX files (wide table).
2) Convert wide segments to per-lesion rows in memory.
3) Compute scores per lesion.
4) Aggregate per patient (SYNTAX/Gensini sum, CAD-RADS max).
5) Merge into original table and save with _评分合并 suffix.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json
import re
import sys
import traceback

import pandas as pd

from single_sheet_processor_v2 import CoronaryScoreCalculator

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception as exc:  # pragma: no cover
    raise RuntimeError("tkinter is required for the file dialog.") from exc


SEGMENT_COLUMN_MAP = {
    "右冠近段": ("RCA", "proximal"),
    "右冠中段": ("RCA", "mid"),
    "右冠远段": ("RCA", "distal"),
    "右冠-后降支": ("PDA", "distal"),
    "右冠-左室后侧支": ("PLV", "distal"),
    "左主干": ("LM", "proximal"),
    "左冠-前降支近段": ("LAD", "proximal"),
    "左冠-前降支中段": ("LAD", "mid"),
    "左冠-前降支远段": ("LAD", "distal"),
    "左冠-第一对角支": ("D", "distal"),
    "左冠-第二对角支": ("D", "distal"),
    "左冠-回旋支近段": ("LCX", "proximal"),
    "左冠-回旋支中段": ("LCX", "mid"),
    "左冠-回旋支远段": ("LCX", "distal"),
    "左冠-第一钝缘支": ("OM", "distal"),
    "左冠-第二钝缘支": ("OM", "distal"),
    "左冠-左房回旋支": ("LCX", "distal"),
    "左冠-左室后侧支": ("PLV", "distal"),
    "左冠-后降支": ("PDA", "distal"),
}


@dataclass
class AggregatedScores:
    patient_id: str
    syntax_score: float
    syntax_class: str
    cad_rads_grade: float
    gensini_score: float
    gensini_class: str


DEFAULT_STSEX_MAP = {
    "1": "male",
    "2": "female",
    "m": "male",
    "male": "male",
    "男": "male",
    "男性": "male",
    "f": "female",
    "female": "female",
    "女": "female",
    "女性": "female",
}


def load_stsex_map() -> dict[str, str]:
    """Load custom stsex mapping from stsex_mapping.json if present."""
    config_path = Path("stsex_mapping.json")
    if not config_path.exists():
        return DEFAULT_STSEX_MAP

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k).strip().lower(): str(v).strip().lower() for k, v in data.items()}
    except Exception:
        return DEFAULT_STSEX_MAP


def normalize_gender(value: object, stsex_map: dict[str, str]) -> str:
    if pd.isna(value):
        return "male"
    value_str = str(value).strip().lower()
    return stsex_map.get(value_str, "male")


STENOSIS_KEYWORDS = ["狭窄", "闭塞", "堵塞", "阻塞", "病变", "肌桥", "正常", "未见狭窄", "无狭窄"]


def extract_stenosis_percent(text: object, use_range_upper: bool = True) -> float | None:
    if pd.isna(text):
        return None

    s = str(text).strip()
    if not s:
        return None

    # Only parse values that look like stenosis statements.
    has_percent = "%" in s
    has_keyword = any(k in s for k in STENOSIS_KEYWORDS)
    if not has_percent and not has_keyword:
        return None

    if any(k in s for k in ["无狭窄", "正常", "未见狭窄"]):
        return 0.0
    if any(k in s for k in ["完全闭塞", "闭塞", "100%", "CTO"]):
        return 100.0
    if "重度" in s or "严重" in s:
        return 90.0
    if "中度" in s:
        return 70.0
    if "轻度" in s:
        return 50.0

    numbers = re.findall(r"\d+\.?\d*", s)
    if not numbers:
        return None

    values = [float(n) for n in numbers]
    if use_range_upper and any(ch in s for ch in ["-", "~", "至", "—", "－"]):
        return max(values)

    return max(values)


def iter_lesions(
    df: pd.DataFrame,
    include_zero: bool,
    stsex_map: dict[str, str],
    error_cb=None,
) -> Iterable[dict]:
    for idx, row in df.iterrows():
        try:
            patient_id = row.get("subjid")
            if pd.isna(patient_id) or str(patient_id).strip() == "":
                raise ValueError("缺少患者ID")
            age = row.get("sys_currentage")
            gender = normalize_gender(row.get("stsex"), stsex_map)

        for col_name, (vessel, location) in SEGMENT_COLUMN_MAP.items():
            if col_name not in df.columns:
                continue

            stenosis = extract_stenosis_percent(row.get(col_name))
            if stenosis is None:
                continue
            if stenosis == 0.0 and not include_zero:
                continue

            yield {
                "patient_id": str(patient_id),
                "age": age,
                "gender": gender,
                "vessel": vessel,
                "location": location,
                "stenosis_percent": float(stenosis),
            }
        except Exception as exc:
            if error_cb:
                error_cb(idx, row.get("subjid"), exc)
            continue


def aggregate_scores(lesions: Iterable[dict]) -> dict[str, AggregatedScores]:
    patients: dict[str, dict] = {}
    for lesion in lesions:
        pid = lesion["patient_id"]
        if pid not in patients:
            patients[pid] = {
                "patient_id": pid,
                "age": lesion.get("age"),
                "gender": lesion.get("gender"),
                "lesions": [],
            }
        patients[pid]["lesions"].append(lesion)

    calculator = CoronaryScoreCalculator()
    aggregated: dict[str, AggregatedScores] = {}

    for pid, patient in patients.items():
        syntax_result = calculator.calculate_syntax_score(patient)
        cad_result = calculator.calculate_cad_rads_grade(patient)
        gensini_result = calculator.calculate_gensini_score(patient)

        aggregated[pid] = AggregatedScores(
            patient_id=pid,
            syntax_score=syntax_result["total_score"],
            syntax_class=syntax_result["risk_category"].title(),
            cad_rads_grade=cad_result["grade"],
            gensini_score=gensini_result["total_score"],
            gensini_class=gensini_result["risk_category"].title(),
        )

    return aggregated


def merge_scores(df: pd.DataFrame, agg: dict[str, AggregatedScores]) -> pd.DataFrame:
    agg_df = pd.DataFrame(
        {
            "patient_id": [v.patient_id for v in agg.values()],
            "SYNTAX_score": [v.syntax_score for v in agg.values()],
            "SYNTAX_class": [v.syntax_class for v in agg.values()],
            "CAD_RADS_grade": [v.cad_rads_grade for v in agg.values()],
            "Gensini_score": [v.gensini_score for v in agg.values()],
            "Gensini_class": [v.gensini_class for v in agg.values()],
        }
    )

    df = df.copy()
    df["subjid"] = df["subjid"].astype(str)
    agg_df["patient_id"] = agg_df["patient_id"].astype(str)

    merged = df.merge(agg_df, left_on="subjid", right_on="patient_id", how="left")
    return merged.drop(columns=["patient_id"])


def read_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def validate_required_columns(df: pd.DataFrame, path: Path) -> None:
    required = {"subjid", "sys_currentage", "stsex"}
    missing = [col for col in required if col not in df.columns]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"缺少必需列: {missing_str} (文件: {path})")


def log_error(
    log_path: Path,
    path: Path,
    exc: Exception,
    row_index: int | None = None,
    patient_id: object | None = None,
) -> None:
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n[FILE] {path}\n")
        if row_index is not None:
            f.write(f"[ROW] {row_index}\n")
        if patient_id is not None:
            f.write(f"[PATIENT] {patient_id}\n")
        f.write(f"[ERROR] {exc}\n")
        f.write(traceback.format_exc())


def write_output(df: pd.DataFrame, input_path: Path) -> Path:
    output_path = input_path.with_name(f"{input_path.stem}_评分合并{input_path.suffix}")
    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        df.to_excel(output_path, index=False)
    else:
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def pick_files(root: tk.Tk) -> list[Path]:
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="选择冠脉造影结果文件",
        filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("All files", "*.*")],
    )
    return [Path(p) for p in paths]


def create_progress_window(root: tk.Tk, total: int) -> tuple[tk.Toplevel, tk.Label, ttk.Progressbar]:
    window = tk.Toplevel(root)
    window.title("处理进度")
    window.geometry("520x120")
    window.resizable(False, False)

    label = tk.Label(window, text="准备开始处理...", anchor="w")
    label.pack(fill="x", padx=12, pady=10)

    bar = ttk.Progressbar(window, mode="determinate", maximum=total)
    bar.pack(fill="x", padx=12, pady=6)

    root.update_idletasks()
    return window, label, bar


def update_progress(
    root: tk.Tk,
    label: tk.Label,
    bar: ttk.Progressbar,
    index: int,
    total: int,
    filename: str,
) -> None:
    label.config(text=f"正在处理 ({index}/{total}): {filename}")
    bar["value"] = index
    root.update_idletasks()
    root.update()


def main() -> int:
    include_zero = False

    root = tk.Tk()
    files = pick_files(root)
    if not files:
        root.destroy()
        print("未选择文件，已退出。")
        return 1

    progress_window, progress_label, progress_bar = create_progress_window(root, len(files))
    stsex_map = load_stsex_map()
    log_path = Path("scoring_errors.log")
    error_summaries: list[str] = []

    for idx, path in enumerate(files, start=1):
        update_progress(root, progress_label, progress_bar, idx, len(files), path.name)
        try:
            df = read_input(path)
            validate_required_columns(df, path)
            def row_error_cb(row_index: int, patient_id: object, exc: Exception) -> None:
                log_error(log_path, path, exc, row_index=row_index, patient_id=patient_id)
                error_summaries.append(
                    f"{path.name} | 行{row_index} | 患者{patient_id} | {exc}"
                )

            lesions = list(
                iter_lesions(
                    df,
                    include_zero=include_zero,
                    stsex_map=stsex_map,
                    error_cb=row_error_cb,
                )
            )
            agg = aggregate_scores(lesions)
            merged = merge_scores(df, agg)
            out_path = write_output(merged, path)
            print(f"已生成: {out_path}")
        except Exception as exc:
            log_error(log_path, path, exc)
            error_summaries.append(f"{path.name} | 文件级错误 | {exc}")
            print(f"处理失败: {path} (已记录到 {log_path})")

    progress_label.config(text="处理完成。")
    root.update_idletasks()
    if error_summaries:
        preview = "\n".join(error_summaries[:8])
        suffix = "\n..." if len(error_summaries) > 8 else ""
        messagebox.showwarning(
            "处理完成（有错误）",
            f"共 {len(error_summaries)} 条错误，已写入 {log_path}\n\n{preview}{suffix}",
        )
    root.after(800, progress_window.destroy)
    root.after(900, root.destroy)

    return 0


if __name__ == "__main__":
    sys.exit(main())
