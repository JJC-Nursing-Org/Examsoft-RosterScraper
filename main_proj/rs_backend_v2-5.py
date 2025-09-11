"""
RosterScraper v3 (modular)
- Targets ExamSoft offline roster HTML, resilient to DOM changes
- Modular extractor strategies + structured logging
- Produces RAW (JSON-per-row) and FINE (columns) CSVs

Run example:
    if __name__ == "__main__":
        OfflineRS(
            inp_name="/mnt/data/example2_new.html",
            exp_folder="/mnt/data/out_mod",
            exp_name="roster_new"
        ).run()

"""

from __future__ import annotations

# this will be used for testing
# import FreeSimpleGUI as sGUI
# import sys

# this is required for the current build
import os
import csv
# import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Sequence
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(out_dir: str, exp_name: str) -> logging.Logger:
    logger = logging.getLogger(f"rosterscraper.{exp_name}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    ch.setFormatter(ch_fmt)
    logger.addHandler(ch)

    # File
    os.makedirs(out_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(out_dir, f"{exp_name}.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fh_fmt)
    logger.addHandler(fh)

    return logger

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StudentRow:
    last_name: str = ""
    first_name: str = ""
    student_id: str = ""
    status: str = ""
    email: str = ""
    date_invited: str = ""
    last_login: str = ""
    last_registered: str = ""
    is_lab_user: str = ""
    is_non_secure: str = ""
    time_multiplier: str = ""
    action: str = ""

    @classmethod
    def from_cellmap(cls, cellmap: Dict[str, str]) -> "StudentRow":
        def yesno(text: Optional[str]) -> str:
            t = (text or "").strip()
            return "Yes" if t else "No"
        s = cellmap.get("status", "").strip()
        return cls(
            last_name=cellmap.get("lastName", "").strip(),
            first_name=cellmap.get("firstName", "").strip(),
            student_id=cellmap.get("studentId", "").strip().zfill(7),
            status=s,
            email=cellmap.get("email", "").strip(),
            date_invited=cellmap.get("dateInvited", "").strip(),
            last_login=cellmap.get("lastLoginDate", "").strip(),
            last_registered=cellmap.get("lastUserRegistration.registrationDate", "").strip(),
            is_lab_user=yesno(cellmap.get("isLabUser")),
            is_non_secure=yesno(cellmap.get("isNonSecure")),
            time_multiplier=cellmap.get("assessmentTimeMultiplier", "").strip(),
            action=s,
        )

# ---------------------------------------------------------------------------
# Extractor strategy interfaces
# ---------------------------------------------------------------------------

class Extractor:
    name: str = "base"
    def extract(self, soup_row) -> Dict[str, str]:
        raise NotImplementedError

class KeyAttrExtractor(Extractor):
    name = "key-attr"
    def extract(self, soup_row) -> Dict[str, str]:
        d: Dict[str, str] = {}
        for el in soup_row.find_all(lambda t: t.has_attr("key") or t.has_attr("data-key")):
            key = el.get("key") or el.get("data-key")
            if not key:
                continue
            txt = el.get_text(" ", strip=True)
            if key == "status":
                txt = txt.replace("●", "").strip()
            d[key] = txt
        return d

class AriaGridExtractor(Extractor):
    name = "aria-grid"
    def extract(self, soup_row) -> Dict[str, str]:
        d: Dict[str, str] = {}
        grid = soup_row.find_parent(lambda t: t.get("role") in ("grid", "table")) or soup_row
        headers_map = {}
        for hdr in grid.find_all(lambda t: t.get("role") == "columnheader"):
            hid = hdr.get("id")
            name = hdr.get_text(" ", strip=True)
            if hid and name:
                headers_map[hid] = name
        cells = soup_row.find_all(lambda t: t.get("role") == "cell")
        for c in cells:
            labelled = c.get("headers")
            if not labelled:
                continue
            label = None
            for hid in labelled.split():
                if hid in headers_map:
                    label = headers_map[hid]
                    break
            if not label:
                continue
            key = normalize_label(label)
            d[key] = c.get_text(" ", strip=True)
        return d

class HtmlTableExtractor(Extractor):
    name = "html-table"
    def extract(self, soup_row) -> Dict[str, str]:
        if soup_row.name != "tr":
            return {}
        table = soup_row.find_parent("table")
        if not table:
            return {}
        # headers
        thead = table.find("thead")
        header_cells = []
        if thead and thead.find("tr"):
            header_cells = thead.find("tr").find_all(["th", "td"])
        else:
            first_tr = table.find("tr")
            if first_tr:
                header_cells = first_tr.find_all(["th", "td"])
        headers = [normalize_label(h.get_text(" ", strip=True)) for h in header_cells]
        # row values
        vals = soup_row.find_all("td")
        d: Dict[str, str] = {}
        for i, td in enumerate(vals):
            if i < len(headers):
                d[headers[i]] = td.get_text(" ", strip=True)
        return d

class LabelValueExtractor(Extractor):
    name = "label-value"
    KNOWN = {
        "Last Name": "lastName",
        "First Name": "firstName",
        "Student ID": "studentId",
        "Email": "email",
        "Status": "status",
        "Date Invited": "dateInvited",
        "Last Login": "lastLoginDate",
        "Last Registered": "lastUserRegistration.registrationDate",
        "Time Multiplier": "assessmentTimeMultiplier",
        "Lab User": "isLabUser",
        "Non-Secure": "isNonSecure",
    }
    def extract(self, soup_row) -> Dict[str, str]:
        d: Dict[str, str] = {}
        for lbl_text, key in self.KNOWN.items():
            node = soup_row.find(lambda t: t.get_text(strip=True) == lbl_text)
            if not node:
                continue
            sib = node.find_next(string=False)
            val = None
            if sib and sib is not node:
                val = sib.get_text(" ", strip=True)
            if not val and node.parent:
                candidates = [x for x in node.parent.find_all(text=False) if x is not node]
                if candidates:
                    val = candidates[-1].get_text(" ", strip=True)
            if val:
                d[key] = val
        return d



# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class OfflineRS:
    def __init__(self,
                 inp_name: Optional[str] = None,
                 exp_folder: Optional[str] = None,
                 exp_name: Optional[str] = None,
                 extractors: Optional[Sequence[Extractor]] = None):
        """GUI-friendly constructor: all args optional; set later via properties.
        - inp_name   (input_html_path) can be assigned after construction
        - exp_folder (output_dir)      can be assigned after construction
        - exp_name   (base_name)       can be assigned after construction
        """
        # private backing fields (can start as None)
        self._inp_name: Optional[str] = inp_name
        self._exp_folder: Optional[str] = exp_folder
        self._exp_name: Optional[str] = exp_name

        # extractor plug-ins
        self.extractors: Sequence[Extractor] = extractors or (
            KeyAttrExtractor(), AriaGridExtractor(), HtmlTableExtractor(), LabelValueExtractor()
        )

        # storage for parsed rows
        self._rows: List[StudentRow] = []

        # logger is bound lazily when we know exp_folder/exp_name
        self.logger: Optional[logging.Logger] = None

    # ------------------------
    # Properties (getters/setters)
    # ------------------------
    @property
    def inp_name(self) -> Optional[str]:
        return self._inp_name

    @inp_name.setter
    def inp_name(self, value: str):
        if not value or not value.lower().endswith(".html"):
            raise ValueError("inp_name must point to an HTML file")
        self._inp_name = value
        # auto-derive exp_name if not set yet
        if not self._exp_name:
            self._exp_name = os.path.splitext(os.path.basename(value))[0]

    @property
    def exp_folder(self) -> Optional[str]:
        return self._exp_folder

    @exp_folder.setter
    def exp_folder(self, value: str):
        if not value:
            raise ValueError("exp_folder cannot be empty")
        os.makedirs(value, exist_ok=True)
        self._exp_folder = value
        self._maybe_rebind_logger()

    @property
    def exp_name(self) -> Optional[str]:
        return self._exp_name

    @exp_name.setter
    def exp_name(self, value: str):
        if not value:
            raise ValueError("exp_name cannot be empty")
        self._exp_name = value
        self._maybe_rebind_logger()

    @property
    def num_stu(self) -> str:
        return str(len(self._rows))

    @property
    def all_stu(self) -> str:
        result = ""
        x = 0

        for r in self._rows:
            x += 1

            result += """
            Entry #{}:
            \t Last Name: {}
            \t First Name: {}
            \t Student ID: {}
            \t Status: {}
            \t Student Email: {}
            \t Date Invited: {}
            \t Last Login: {}
            \t Last Registered: {} 
            \t Lab User: {}         
            \t Non-Secure User: {}
            \t Time Multiplier: {}
            \t Action: {}            
            \n""".format(
                x, r.last_name,r.first_name,r.student_id,r.status,r.email,
                    r.date_invited,r.last_login,r.last_registered,r.is_lab_user,
                    r.is_non_secure,r.time_multiplier,r.action
            )
            # print(result)

        # result = ' '.join(map(str, self._rows))
        return result

    # ------------------------
    # Public API
    # ------------------------
    def run(self) -> None:
        self._ensure_ready()
        rows, raw_dicts = self._parse_html()
        self._rows = rows
        self._write_raw(raw_dicts)
        self._write_fine(rows)
        assert self.logger is not None
        self.logger.info("Done. Wrote %s rows.", self.num_stu)

    # ------------------------
    # Internal helpers
    # ------------------------
    def _ensure_ready(self) -> None:
        """Fill in sensible defaults and (re)bind logger before parsing."""
        if not self._inp_name:
            raise ValueError("inp_name (input HTML path) must be set before run()")
        # defaults for export folder/name
        if not self._exp_folder:
            # default to the folder of the input file; fallback to CWD
            base_dir = os.path.dirname(self._inp_name) or os.getcwd()
            self._exp_folder = os.path.join(base_dir, "out")
        os.makedirs(self._exp_folder, exist_ok=True)
        if not self._exp_name:
            self._exp_name = os.path.splitext(os.path.basename(self._inp_name))[0]
        self._maybe_rebind_logger()

    def _maybe_rebind_logger(self) -> None:
        """(Re)create the file+console logger if folder/name are available."""
        if self._exp_folder and self._exp_name:
            self.logger = setup_logger(self._exp_folder, self._exp_name)
        elif self.logger is None:
            # minimal console logger until we know where to write the file
            lg = logging.getLogger("rosterscraper.temp")
            if not lg.handlers:
                lg.setLevel(logging.INFO)
                ch = logging.StreamHandler()
                ch.setLevel(logging.INFO)
                ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
                lg.addHandler(ch)
            self.logger = lg

#     def _out_path(self, suffix: str) -> str:
#         assert self._exp_folder and self._exp_name
#         return os.path.join(self._exp_folder, f"{self._exp_name}_{suffix}")
# self) -> None:
#         rows, raw_dicts = self._parse_html()
#         self._write_raw(raw_dicts)
#         self._write_fine(rows)
#         self.logger.info("Done. Wrote %d rows.", len(rows))

    def _out_path(self, suffix: str, ext: str = "csv") -> str:
        """
        Build a full path for an output file.

        Args:
            suffix: label to append after exp_name (e.g., "raw", "fine").
            ext: file extension, default "csv".

        Returns:
            Full filesystem path as string.
        """
        if not self._exp_folder or not self._exp_name:
            raise ValueError("exp_folder and exp_name must be set before building output paths")
        filename = f"{self._exp_name}_{suffix}.{ext}"
        return os.path.join(self._exp_folder, filename)

    # ---------- Parsing ----------
    def _parse_html(self) -> (List[StudentRow], List[Dict[str, str]]):
        with open(self.inp_name, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f, "html.parser")

        # try multiple row container patterns
        row_candidates = (
            soup.find_all(lambda t: t.name == "app-grid-row")
            or soup.find_all(lambda t: t.name == "grid-row")
            or soup.find_all(lambda t: t.get("role") == "row")
        )
        if not row_candidates:
            row_candidates = soup.find_all(lambda t: t.name in ("tr",))

        self.logger.info("Found %d row candidates", len(row_candidates))

        rows: List[StudentRow] = []
        raw_dicts: List[Dict[str, str]] = []
        used_counts: Dict[str, int] = {ex.name: 0 for ex in self.extractors}
        unknown_keys: Dict[str, int] = {}

        for idx, rc in enumerate(row_candidates, start=1):
            content = rc.find("div", class_="grid-row__content") or rc
            cellmap: Dict[str, str] = {}
            used_extractor: Optional[str] = None
            for ex in self.extractors:
                cellmap = ex.extract(content)
                if cellmap:
                    used_extractor = ex.name
                    used_counts[ex.name] += 1
                    break
            if not cellmap:
                self.logger.warning("Row %d: no extractor matched; skipping", idx)
                continue

            # track unknown keys
            for k in cellmap.keys():
                if k not in _LABEL_MAP.values() and k not in ("lastName","firstName","studentId","email","status","dateInvited","lastLoginDate","lastUserRegistration.registrationDate","assessmentTimeMultiplier","isLabUser","isNonSecure","actions"):
                    unknown_keys[k] = unknown_keys.get(k, 0) + 1

            raw_dicts.append(cellmap)
            rows.append(StudentRow.from_cellmap(cellmap))
            self.logger.debug("Row %d parsed via %s", idx, used_extractor)

        # summary logs
        for name, count in used_counts.items():
            self.logger.info("Extractor %-12s used on %d rows", name, count)
        if unknown_keys:
            self.logger.info("Unknown keys detected: %s", ", ".join(f"{k}({c})" for k,c in unknown_keys.items()))

        return rows, raw_dicts

    # ---------- Writers ----------
    def _write_raw(self, raw_dicts: List[Dict[str, str]]) -> None:
        raw_path = self._out_path("raw", "csv")

        # Union of keys across all rows
        union_keys: set[str] = set()
        for d in raw_dicts:
            union_keys.update(d.keys())

        # Prefer these first (if present), then any extras in alpha order
        preferred = [
            "lastName", "firstName", "studentId", "email", "status",
            "dateInvited", "lastLoginDate", "lastUserRegistration.registrationDate",
            "assessmentTimeMultiplier", "isLabUser", "isNonSecure", "actions",
        ]
        extras = sorted(k for k in union_keys if k not in preferred)
        headers = [k for k in preferred if k in union_keys] + extras

        with open(raw_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';',
                                    quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
            writer.writeheader()
            for d in raw_dicts:
                # ensure missing keys become empty cells
                row = {h: d.get(h, "") for h in headers}
                writer.writerow(row)

        assert self.logger is not None
        self.logger.info("Wrote RAW (CSV wide): %s", raw_path)

    # if I wanted to switch to writing out JSON instead:

    # def _write_raw_jsonl(self, raw_dicts: List[Dict[str, str]]) -> None:
    #     raw_path = self._out_path("raw", "jsonl")
    #     with open(raw_path, "w", encoding="utf-8", newline="") as f:
    #         for obj in raw_dicts:
    #             f.write(json.dumps(obj, ensure_ascii=False))
    #             f.write("\n")
    #     assert self.logger is not None
    #     self.logger.info("Wrote RAW (JSONL): %s", raw_path)

        # self.logger.info("Wrote RAW: %s", raw_path)

    def _write_fine(self, rows: List[StudentRow]) -> None:
        # fine_path = os.path.join(self.exp_folder, f"{self.exp_name}_fine.csv")
        fine_path = self._out_path("fine")
        headers = [
            "Last Name","First Name","Student ID","Status","Student Email",
            "Date Invited","Last Login","Last Registered","Lab User",
            "Non-Secure User","Time Multiplier","Action",
        ]
        with open(fine_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            for r in rows:
                writer.writerow([
                    r.last_name,r.first_name,r.student_id,r.status,r.email,
                    r.date_invited,r.last_login,r.last_registered,r.is_lab_user,
                    r.is_non_secure,r.time_multiplier,r.action,
                ])
        self.logger.info("Wrote FINE: %s", fine_path)


# if __name__ == "__main__":
#     sGUI.theme('Dark2')
#
#     obj = OfflineRS()
#
#     if len(sys.argv) == 1:
#         event, values = sGUI.Window('Import Examsoft HTML File',
#                                     [[sGUI.Text('Document to open')],
#                                      [sGUI.In(), sGUI.FileBrowse()],
#                                      [sGUI.Open(), sGUI.Cancel()]]).read(close=True)
#         f_name = values[0]
#     else:
#         f_name = sys.argv[1]
#
#     if not f_name:
#         sGUI.popup_error("Cancelling: no filename supplied.", title="Program Exiting Now.")
#         raise SystemExit("Cancelling: no filename supplied")
#     else:
#         sGUI.popup('The filename you chose was: ', f_name)
#         obj.inp_name = (f_name)
#
#     obj.exp_folder = (sGUI.popup_get_folder("Output Folder for CSV's:"))
#     obj.exp_name = (sGUI.popup_get_text("Name your CSV's:"))
#
#     obj.run()
#     sys.exit()
