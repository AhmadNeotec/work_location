# Copyright (c) 2026, Neotec and contributors
# For license information, please see license.txt

import frappe
import datetime
from frappe import _
from frappe.utils import logger

logger.set_log_level("debug")
logger = frappe.logger("EC Report", allow_site=True, file_count=1)

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    processed_data = process_data(data, filters)
    return columns, processed_data

def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql("""
        SELECT
            ec.employee,
            ec.employee_name,
            ee.department,
            ec.creation,
            ec.time,
            ec.log_type,
            ec.shift
        FROM
            `tabEmployee Checkin` ec
        INNER JOIN
            `tabEmployee` ee
        ON
            ec.employee = ee.name
        WHERE ee.docstatus < 2
            %s
        ORDER BY
            ec.creation DESC
        """ % conditions, filters, as_dict=1)
    return data

def get_shift_details(shift_name):
    if not shift_name:
        return None

    shift = frappe.get_doc("Shift Type", shift_name)
    return {
        "shift_start_time": shift.start_time,
        "shift_end_time": shift.end_time,
        "begin_check_in_before_shift_start_time": shift.begin_check_in_before_shift_start_time,
        "allow_check_out_after_shift_end_time": shift.allow_check_out_after_shift_end_time,
        "late_entry_grace_period": shift.late_entry_grace_period,
        "early_exit_grace_period": shift.early_exit_grace_period,
        "regular_daily_hours": shift.end_time - shift.start_time
    }

def process_data(data, filters):
    processed_data = []
    employee_entries = {}
    hr_format = filters.get("hr_format", "24 hr")

    for entry in data:
        employee = entry.employee
        day = entry.creation.date()
        if employee not in employee_entries:
            employee_entries[employee] = {}
        if day not in employee_entries[employee]:
            employee_entries[employee][day] = {"time_in": None, "time_out": None, "entries": [], "regular_daily_hours": None}

        if entry.log_type == "IN":
            if not employee_entries[employee][day]["time_in"]:
                employee_entries[employee][day]["time_in"] = entry.time
        elif entry.log_type == "OUT":
            if employee_entries[employee][day]["time_in"] and entry.time < employee_entries[employee][day]["time_in"]:
                employee_entries[employee][day]["time_out"] = None
            else:
                employee_entries[employee][day]["time_out"] = entry.time

        employee_entries[employee][day]["entries"].append(entry)

    for employee, days in employee_entries.items():
        employee_indent = {"employee": f"{employee}", "indent": 0}
        processed_data.append(employee_indent)
        for day, day_data in days.items():
            if day_data["time_out"] and day_data["time_in"] and day_data["time_out"] < day_data["time_in"]:
                day_data["time_out"] = None

            shift_details = get_shift_details(day_data["entries"][0].shift)
            if shift_details:
                day_data["regular_daily_hours"] = shift_details["regular_daily_hours"]

                start_time = datetime.datetime.strptime(day_data["entries"][0].creation.strftime("%Y-%m-%d") + " " + str(shift_details["shift_start_time"]), "%Y-%m-%d %H:%M:%S")
                end_time = datetime.datetime.strptime(day_data["entries"][0].creation.strftime("%Y-%m-%d") + " " + str(shift_details["shift_end_time"]), "%Y-%m-%d %H:%M:%S")

                if day_data["time_in"]:
                    late_entry_grace_period = datetime.timedelta(minutes=shift_details["late_entry_grace_period"])
                    if day_data["time_in"] > start_time + late_entry_grace_period:
                        day_data["late_entry"] = day_data["time_in"] - start_time

                if day_data["time_out"]:
                    early_exit_grace_period = datetime.timedelta(minutes=shift_details["early_exit_grace_period"])
                    if day_data["time_out"] < end_time - early_exit_grace_period:
                        day_data["early_exit"] = end_time - day_data["time_out"]
                    if day_data["time_out"] > end_time + datetime.timedelta(minutes=shift_details["allow_check_out_after_shift_end_time"]):
                        day_data["missed_checkout"] = True
                    
                if not day_data["time_out"]:
                    day_data["missed_checkout"] = True

                if day_data["time_out"] and day_data["time_out"] > end_time:
                    day_data["extra_hours"] = day_data["time_out"] - end_time

            total_hours = None
            if day_data['time_in']:
                total_hours = day_data["time_out"] - day_data["time_in"] if day_data["time_out"] else None
                total_hours = format_timedelta(total_hours) if total_hours else None

            processed_data.append({
                "employee": day_data["entries"][0].employee,
                "employee_name": day_data["entries"][0].employee_name,
                "department": day_data["entries"][0].department,
                "creation": day_data["entries"][0].creation,
                "date": day,
                "day": day_data["entries"][0].creation.strftime("%A"),
                "regular_daily_hours": day_data["regular_daily_hours"],
                "time_in": format_time(day_data["time_in"], hr_format) if day_data["time_in"] else None,
                "time_out": format_time(day_data["time_out"], hr_format) if day_data["time_out"] else None,
                "total_hours": total_hours,
                "late_entry": format_timedelta(day_data.get("late_entry")),
                "early_exit": format_timedelta(day_data.get("early_exit")),
                "missed_checkout": day_data.get("missed_checkout"),
                "extra_hours": format_timedelta(day_data.get("extra_hours")),
                "indent": 1
            })

    return processed_data

def format_time(time, hr_format):
    if hr_format == "12 hr":
        return time.strftime("%I:%M:%S %p")
    else:
        return time.strftime("%H:%M:%S")

def format_timedelta(td):
    if td:
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return None

def get_columns(filters):
    columns = [
        {
            "label": _("Employee ID"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 200
        },
        {
            "label": _("Creation"),
            "fieldname": "creation",
            "fieldtype": "Datetime",
            "width": 180
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Day"),
            "fieldname": "day",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Regular Daily Hours"),
            "fieldname": "regular_daily_hours",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Time-In"),
            "fieldname": "time_in",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Time-Out"),
            "fieldname": "time_out",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Total Hours"),
            "fieldname": "total_hours",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Late Entry"),
            "fieldname": "late_entry",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Early Exit"),
            "fieldname": "early_exit",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Missed Checkout"),
            "fieldname": "missed_checkout",
            "fieldtype": "Boolean",
            "width": 180
        },
        {
            "label": _("Extra Hours"),
            "fieldname": "extra_hours",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Indent"),
            "fieldname": "indent",
            "fieldtype": "Int",
            "hidden": 1
        }
    ]
    return columns

def get_conditions(filters):
    conditions = ""
    if filters.get("employee"):
        conditions += " AND ec.employee = %(employee)s"
    if filters.get("from_date"):
        conditions += " AND ec.creation >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND ec.creation <= %(to_date)s"
    if filters.get("department"):
        conditions += " AND ee.department = %(department)s"
    return conditions