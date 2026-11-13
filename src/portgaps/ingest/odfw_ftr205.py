"""Parse ODFW FTR205 'Pounds and values ... landed in Oregon - <PORT>' PDFs into long cells.

Output: one row per table x row label x measure x month, with value or blank.
Blank = no number printed in that cell (ODFW gives no suppression flag).
Columns are assigned by nearest month-header centre; each row is checked against its printed Total.
Usage: python -I odfw_ftr205.py <pdf_dir> <out_csv>
"""
import csv, re, sys
from pathlib import Path
import pdfplumber

MONTHS = ["January","February","March","April","May","June","July","August",
          "September","October","November","December","Total"]
NUM = re.compile(r"^-?[\d,]+$")

def parse_pdf(path):
    rows = []  # dicts
    title = None; year = None; status = None
    cur_cat = None; last_label = None; rights = None
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
            text = page.extract_text() or ""
            m = re.search(r"LANDED IN OREGON\s*(?:-\s*)?(?:IN\s+)?(?:THE\s+)?(.+?)\n\s*\n?\s*January", text, re.S)
            if m and title is None:
                title = " ".join(m.group(1).split())
            my = re.search(r"(\d{4})\s+(FINAL|PRELIMINARY|PRELIM)", text, re.I)
            if my and year is None:
                year = int(my.group(1)); status = my.group(2).upper()
            jan = [w for w in words if w["text"] == "January"]
            hdr = {}
            if jan:
                hdr_top = jan[0]["top"]
                hdr = {w["text"]: w for w in words if w["text"] in MONTHS and abs(w["top"] - hdr_top) < 3}
            if len(hdr) == 13:
                rights = [hdr[mn]["x1"] for mn in MONTHS]
            elif rights is not None and last_label is not None:
                # T2.1 fix: a row spilled onto a final page with no month header
                # (e.g. the "$" Total row in 2016 Charleston, 2019 Waldport-Winchester Bay).
                # Reuse the previous page's column positions; the row-total check still applies.
                meas_top = [w["top"] for w in words if w["text"] in ("#", "$")]
                if not meas_top:
                    continue
                hdr_top = min(meas_top) - 6
            else:
                continue
            # bucket words into lines by 'top'
            body = [w for w in words if w["top"] > hdr_top + 5 and not w["text"].startswith("Data")]
            lines = {}
            for w in body:
                key = round(w["top"] / 3)
                lines.setdefault(key, []).append(w)
            for key in sorted(lines):
                ws = sorted(lines[key], key=lambda w: w["x0"])
                meas = [w for w in ws if w["text"] in ("#", "$")]
                if not meas:
                    continue
                mx = meas[0]["x0"]
                label_ws = [w for w in ws if w["x1"] < mx]
                nums = [w for w in ws if w["x0"] > meas[0]["x1"] and NUM.match(w["text"])]
                if label_ws:
                    label = " ".join(w["text"] for w in label_ws)
                    indent = label_ws[0]["x0"]
                    if label == "Total":
                        level = "grand_total"
                    elif indent < 25:
                        level = "category"; cur_cat = label
                    else:
                        level = "species"
                    last_label = (label, level, cur_cat if level == "species" else label)
                if last_label is None:
                    continue
                label, level, cat = last_label
                cells = [None] * 13
                for w in nums:
                    # numbers are right-aligned under the header's right edge
                    j = min(range(13), key=lambda k: abs(rights[k] - w["x1"]))
                    if abs(rights[j] - w["x1"]) > 12:
                        raise ValueError(f"{path.name} p{pno} {label}: number {w['text']} at x1={w['x1']:.0f} not under a column")
                    if cells[j] is not None:
                        raise ValueError(f"{path.name} p{pno} {label}: two numbers in {MONTHS[j]}")
                    cells[j] = int(w["text"].replace(",", ""))
                rows.append(dict(file=path.name, page=pno, table_title=title, year=year, status=status,
                                 level=level, category=cat, label=label, measure=meas[0]["text"], cells=cells))
    return rows

def main(pdf_dir, out_csv):
    out = []; problems = []
    for p in sorted(Path(pdf_dir).glob("t21_odfw_*.pdf")):
        try:
            rs = parse_pdf(p)
        except Exception as e:
            problems.append((p.name, str(e))); continue
        for r in rs:
            mon = r["cells"][:12]; tot = r["cells"][12]
            s = sum(v for v in mon if v is not None)
            ok = (tot is None and s == 0) or (tot is not None and abs(s - tot) <= 2)
            if not ok:
                problems.append((p.name, f"p{r['page']} {r['label']} {r['measure']} sum {s} != total {tot}"))
            for i in range(12):
                out.append(dict(file=r["file"], page=r["page"], table_title=r["table_title"], year=r["year"],
                                status=r["status"], level=r["level"], category=r["category"], label=r["label"],
                                measure="pounds" if r["measure"] == "#" else "value_usd", month=i + 1,
                                value="" if mon[i] is None else mon[i], row_total=tot if tot is not None else "",
                                row_check="ok" if ok else "sum_mismatch"))
    for pr in problems[:80]:
        print("  ", pr)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(len(out), "cells;", len(problems), "problems")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
