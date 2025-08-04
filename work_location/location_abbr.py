import frappe
from frappe.model.naming import make_autoname

def abbreviate(name):
    return ''.join([x[0].upper() for x in name.split() if x.isalpha()])[:4]

def autoname(doc, method=None):
    if doc.name:
        return  # skip if already named
    abbr = abbreviate(doc.location_name or "")
    doc.name = make_autoname(f"LOC-.{abbr}.-.####")
