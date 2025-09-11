from typing import List, Dict, Optional, Sequence
from bs4 import BeautifulSoup
from main_proj.backend.rs_utils import UtilsRS

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
            key = UtilsRS().normalize_label(label)
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
        headers = [UtilsRS().normalize_label(h.get_text(" ", strip=True)) for h in header_cells]
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