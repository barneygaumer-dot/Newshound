import re

HIGH = [
    r"\bearnings\b", r"\bguidance\b", r"\bmerger\b", r"\bacquisition\b",
    r"\bFDA\b", r"\bapproval\b", r"\binvestigation\b", r"\brecall\b",
    r"\boffering\b", r"\bbankrupt", r"\bhalt", r"\b8-K\b", r"\bCEO\b",
    r"\bCFO\b", r"\bsanction", r"\bsubpoena\b"
]
MED = [r"\banalyst\b", r"\bprice target\b", r"\bcontract\b", r"\bpartnership\b", r"\blaunch\b"]

def infer_importance(title, supplied=None):
    if supplied:
        s = str(supplied).upper()
        if s in {"HIGH","MEDIUM","LOW"}:
            return s
    for p in HIGH:
        if re.search(p, title or "", re.I):
            return "HIGH"
    for p in MED:
        if re.search(p, title or "", re.I):
            return "MEDIUM"
    return "LOW"

def category(title, tags=None, form=None):
    t = (title or "").lower()
    if form:
        return f"SEC {form}"
    if any(x in t for x in ("fda","recall","investigation","regulator","nhtsa")):
        return "REGULATORY"
    if any(x in t for x in ("earnings","revenue","eps","guidance")):
        return "EARNINGS"
    if any(x in t for x in ("analyst","price target","upgrade","downgrade")):
        return "ANALYST"
    if any(x in t for x in ("offering","dilution","shares","convertible")):
        return "CAPITAL"
    return "MARKET NEWS"
