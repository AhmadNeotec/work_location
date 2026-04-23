# Copyright (c) 2026, Neotec and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, get_datetime, formatdate

def execute(filters=None):
    if not filters:
        filters = {"date": nowdate()}  # Ensures there's always a date

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Employee Code", "fieldname": "employee_code", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 120},
        {"label": "Present", "fieldname": "present", "fieldtype": "Data", "width": 80},
        {"label": "Checkin Date", "fieldname": "checkin_date", "fieldtype": "Date", "width": 120},
        {"label": "Checkin Time", "fieldname": "checkin_time", "fieldtype": "Time", "width": 120},
        {"label": "Late By (Min)", "fieldname": "late_by", "fieldtype": "Int", "width": 100},
        {"label": "Last Checkout Time", "fieldname": "last_checkout", "fieldtype": "Time", "width": 150},
        {"label": "Early By (Min)", "fieldname": "early_by", "fieldtype": "Int", "width": 100}
    ]

def get_data(filters):
    date_filter = filters.get("date", nowdate())  # Use the provided date or today if not specified

    query = f"""
        SELECT
            emp.name as employee_code, emp.employee_name,
            IFNULL(checkin.shift, 'No Shift') as shift,
            MIN(checkin.time) as first_checkin,
            DATE(MIN(checkin.time)) as checkin_date,
            TIME(MIN(checkin.time)) as checkin_time,
            MAX(checkin.time) as last_checkout_time,
            TIME(MAX(checkin.time)) as last_checkout,
            COUNT(checkin.name) as checkin_count,
            checkin.shift_start, checkin.shift_end
        FROM
            `tabEmployee` emp
        LEFT JOIN
            `tabEmployee Checkin` checkin ON emp.name = checkin.employee AND checkin.docstatus = 0
            AND DATE(checkin.time) = '{date_filter}'
        WHERE
            (emp.status = 'Active' OR checkin.name IS NOT NULL)
        GROUP BY emp.name, checkin.shift
    """
    data = frappe.db.sql(query, as_dict=1)
    
    for d in data:
        is_present = d['checkin_count'] > 0
        d['present'] = "P" if is_present else "A"
        if is_present:
            d['checkin_date'] = formatdate(d['checkin_date'], "dd-mm-yyyy") if d['checkin_date'] != None else 'No Date'
        else:
            d['checkin_date'] = 'No Date'

        if d['checkin_count'] > 1:
            d['last_checkout'] = d['last_checkout']
            d['early_by'] = calculate_early_by(d['last_checkout_time'], d['shift_end'])
        else:
            d['last_checkout'] = None
            d['early_by'] = 0  # No valid checkout time to calculate 'Early By'

        d['late_by'] = calculate_time_diff(d['first_checkin'], d['shift_start']) if is_present else 0

    return data

def calculate_time_diff(check_time, shift_time, early=False):
    if isinstance(check_time, str) or isinstance(shift_time, str):
        return 0  # Return 0 if either time is a string indicating 'No Time'
    
    if check_time and shift_time:
        time_diff = (get_datetime(check_time) - get_datetime(shift_time)).total_seconds()
        if early:
            time_diff = -time_diff
        return max(int(time_diff / 60), 0)
    return 0

def calculate_early_by(checkout_time, shift_end):
    if checkout_time and shift_end:
        end_time = get_datetime(shift_end)
        last_check_time = get_datetime(checkout_time)
        if last_check_time < end_time:
            time_diff = (end_time - last_check_time).total_seconds()
            return max(int(time_diff / 60), 0)
    return 0
