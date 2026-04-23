# Copyright (c) 2026, Neotec and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_data(filters):
# Build dynamic conditions based on filters provided by the user in the UI. This allows for flexible querying of
# Employee Checkin records based on employee, date range, shift, and log type. The conditions are safely parameterized to prevent SQL injection.
    conditions = get_conditions(filters)
    return frappe.db.sql(
        f"""
        SELECT
            ec.name AS checkin_id,
            ec.employee AS employee,
            ec.employee_name AS employee_name,
            ee.department AS department,
            ec.custom_checkin_location AS location,
            ec.shift AS shift,
            ec.log_type AS log_type,
            ec.time AS time,
            ec.device_id AS device_id
        FROM `tabEmployee Checkin` ec
        LEFT JOIN `tabEmployee` ee
            ON ec.employee = ee.name
        WHERE ec.docstatus < 2
            {conditions}
        ORDER BY ec.time DESC, ec.employee ASC
        """,
        filters,
        as_dict=True,
    )


def get_conditions(filters):
    conditions = ""

    if filters.get("employee"):
        conditions += " AND ec.employee = %(employee)s"

    # Date range (required by UI, but keep safe defaults)
    if filters.get("from_date"):
        conditions += " AND DATE(ec.time) >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND DATE(ec.time) <= %(to_date)s"

    if filters.get("shift"):
        conditions += " AND ec.shift = %(shift)s"

    if filters.get("log_type"):
        conditions += " AND ec.log_type = %(log_type)s"

    return conditions


def get_columns():
    return [
        {
            "label": _("Checkin"),
            "fieldname": "checkin_id",
            "fieldtype": "Link",
            "options": "Employee Checkin",
            "width": 140,
        },
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120,
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 140,
        },
        {
            "label": _("Location"),
            "fieldname": "location",
            "fieldtype": "Link",
            "options": "Location",
            "width": 140,
        },
        {
            "label": _("Shift"),
            "fieldname": "shift",
            "fieldtype": "Link",
            "options": "Shift Type",
            "width": 140,
        },
        {
            "label": _("Log Type"),
            "fieldname": "log_type",
            "fieldtype": "Data",
            "width": 90,
        },
        {
            "label": _("Time"),
            "fieldname": "time",
            "fieldtype": "Datetime",
            "width": 170,
        },
        {
            "label": _("Device ID"),
            "fieldname": "device_id",
            "fieldtype": "Data",
            "width": 140,
        },
    ]