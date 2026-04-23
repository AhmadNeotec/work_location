# Copyright (c) 2026, Neotec and contributors
# For license information, please see license.txt

import frappe
import datetime
from frappe import _
from frappe.utils import getdate, get_datetime, flt, time_diff_in_hours  # type: ignore

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql("""
        SELECT
            ec.employee,
            ec.employee_name,
            ee.department,
            DATE(ec.time) as date,
            ec.log_type,
            ec.time,
            ec.name as checkin_name,
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
            ec.employee, DATE(ec.time), ec.time
        """ % conditions, filters, as_dict=1)

    processed_data = process_data(data, filters)
    return processed_data

def process_data(data, filters):
# Group check-ins by employee and date to calculate daily attendance metrics such as total work hours, break hours, target hours, and attendance status. This involves pairing IN and OUT check-ins, calculating time differences, and determining overall presence or absence for the day.
    employee_days = {}
    for entry in data:
        key = (entry.employee, entry.date)
        if key not in employee_days:
            employee_days[key] = {
                'employee': entry.employee,
                'employee_name': entry.employee_name,
                'department': entry.department,
                'date': entry.date,
                'checkins': [],
                'shift': entry.shift
            }
        employee_days[key]['checkins'].append({
            'time': entry.time,
            'log_type': entry.log_type,
            'name': entry.checkin_name
        })

    result = []
    for key, day_data in employee_days.items():
        row = calculate_day_metrics(day_data)
        result.append(row)

    return result

def calculate_day_metrics(day_data):
    checkins = sorted(day_data['checkins'], key=lambda x: x['time'])
    ins = [c for c in checkins if c['log_type'] == 'IN']
    outs = [c for c in checkins if c['log_type'] == 'OUT']

    first_checkin = ins[0]['time'] if ins else None
    last_checkout = outs[-1]['time'] if outs else None

    total_work_hours = 0
    break_hours = 0

    if ins and outs:
        # Pair IN and OUT
        paired_times = []
        for i in range(len(ins)):
            if i < len(outs):
                paired_times.append((ins[i]['time'], outs[i]['time']))

        for start, end in paired_times:
            total_work_hours += time_diff_in_hours(end, start)

        # Calculate breaks: time between OUT and next IN
        # Guard against mismatch in counts (more OUTs than INs, etc.)
        if len(outs) > 1 and len(ins) > 1:
            max_break_pairs = min(len(outs) - 1, len(ins) - 1)
            for i in range(max_break_pairs):
                break_start = outs[i]['time']
                break_end = ins[i + 1]['time']
                break_hours += time_diff_in_hours(break_end, break_start)

    # Target Hours from Shift
    target_hours = get_target_hours(day_data['shift'], day_data['date'])

    difference = total_work_hours - target_hours if target_hours else 0

    # Attendance Status
    if first_checkin:
        attendance_status = "Present"
    else:
        attendance_status = "Absent"

    # Check for leaves
    leaves = frappe.get_all("Leave Application", filters={
        'employee': day_data['employee'],
        'from_date': ["<=", day_data['date']],
        'to_date': [">=", day_data['date']],
        "status": "Approved"
    }, fields=["leave_type"])
    if leaves:
        attendance_status = leaves[0].leave_type

    # Attendance Record Reference
    ref = ", ".join([c['name'] for c in checkins])

    # Overall Presence / Absence
    overall = "Present" if attendance_status == "Present" else "Absent"

    return {
        "date": day_data['date'],
        "employee_id": day_data['employee'],
        "attendance_status": attendance_status,
        "total_work_hours": round(total_work_hours, 2),
        "break_hours": round(break_hours, 2),
        "target_hours": round(target_hours, 2) if target_hours else 0,
        "difference": round(difference, 2),
        "first_check_in_time": first_checkin.strftime("%H:%M:%S") if first_checkin else None,
        "last_check_out_time": last_checkout.strftime("%H:%M:%S") if last_checkout else None,
        "attendance_record_reference": ref,
        "overall_presence_absence": overall
    }

def get_target_hours(shift_name, date):
    if not shift_name:
        return 0
    shift = frappe.get_doc("Shift Type", shift_name)
    # Assuming working hours are end_time - start_time
    if shift.end_time and shift.start_time:
        return (shift.end_time - shift.start_time).total_seconds() / 3600
    return 0

def get_conditions(filters):
    conditions = ""
    if filters.get("employee"):
        conditions += " AND ec.employee = %(employee)s"
    if filters.get("from_date"):
        conditions += " AND DATE(ec.time) >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND DATE(ec.time) <= %(to_date)s"
    if filters.get("department"):
        conditions += " AND ee.department = %(department)s"
    if filters.get("shift"):
        conditions += " AND ec.shift = %(shift)s"
    return conditions

def get_columns():
    columns = [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Employee ID"),
            "fieldname": "employee_id",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "label": _("Attendance Status"),
            "fieldname": "attendance_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Total Work Hours"),
            "fieldname": "total_work_hours",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Break Hours"),
            "fieldname": "break_hours",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Target Hours"),
            "fieldname": "target_hours",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Difference"),
            "fieldname": "difference",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("First Check-in Time"),
            "fieldname": "first_check_in_time",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Last Check-out Time"),
            "fieldname": "last_check_out_time",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Attendance Record Reference"),
            "fieldname": "attendance_record_reference",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Overall Presence / Absence"),
            "fieldname": "overall_presence_absence",
            "fieldtype": "Data",
            "width": 150
        }
    ]
    return columns