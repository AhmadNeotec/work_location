import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import getdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_data(filters):
    # Get data directly from Attendance doctype
    conditions = get_conditions(filters)
    
    attendance_data = frappe.db.sql(
        f"""
        SELECT 
            att.name AS reference,
            att.employee AS employee,
            att.employee_name AS employee_name,
            att.attendance_date AS attendance_date,
            att.status AS status,
            att.in_time AS in_time,
            att.out_time AS out_time,
            att.shift AS shift_type,
            att.working_hours AS working_hours
        FROM `tabAttendance` att
        WHERE att.docstatus < 2
            {conditions}
        ORDER BY att.attendance_date ASC, att.employee ASC
        """,
        filters,
        as_dict=True,
    )
    
    # Build result data
    result_data = []
    
    for att in attendance_data:
        # Calculate late entry and early exit times from in_time/out_time
        late_entry, early_exit, overtime = calculate_time_differences(
            att.in_time,
            att.out_time,
            att.shift_type,
            att.attendance_date
        )
        
        # Add HTML color formatting to status
        status_with_color = get_status_with_color(att.status)
        
        result_data.append({
            "reference": att.reference,
            "employee": att.employee,
            "employee_name": att.employee_name,
            "attendance_date": att.attendance_date,
            "status": status_with_color,
            "status_raw": att.status,
            "check_in": att.in_time,
            "check_out": att.out_time,
            "shift_in": None,
            "shift_out": None,
            "late_entry": late_entry,
            "early_exit": early_exit,
            "overtime": overtime,
            "working_hours": f"{att.working_hours}h" if att.working_hours else "-",
            "shift_type": att.shift_type,
        })
    
    # Sort by date
    result_data.sort(key=lambda x: x.get("attendance_date") or datetime.min)
    
    # Apply status filter if needed
    if filters.get("status") and filters.get("status") != "ALL":
        status_filter = filters.get("status")
        result_data = [d for d in result_data if d.get("status_raw") == status_filter]
    
    return result_data


def calculate_time_differences(in_time, out_time, shift_type, attendance_date):
    """Calculate late entry, early exit, and overtime in HH:MM format"""
    late_entry = "-"
    early_exit = "-"
    overtime = "-"
    
    if not shift_type:
        return late_entry, early_exit, overtime
    
    # Get shift details
    shift = frappe.db.sql(
        """
        SELECT start_time, end_time
        FROM `tabShift Type`
        WHERE name = %s
        """,
        (shift_type,),
        as_dict=True,
    )
    
    if not shift:
        return late_entry, early_exit, overtime
    
    shift_start = shift[0].start_time
    shift_end = shift[0].end_time
    
    # Convert timedelta to time
    if isinstance(shift_start, timedelta):
        shift_start_time = (datetime.min + shift_start).time()
    else:
        shift_start_time = shift_start
    
    if isinstance(shift_end, timedelta):
        shift_end_time = (datetime.min + shift_end).time()
    else:
        shift_end_time = shift_end
    
    # Calculate late entry (if in_time > shift_start)
    if in_time and in_time.time() > shift_start_time:
        late_delta = datetime.combine(in_time.date(), in_time.time()) - \
                    datetime.combine(in_time.date(), shift_start_time)
        late_minutes = round(late_delta.total_seconds() / 60)
        late_entry = format_minutes_to_hhmm(late_minutes)
    
    # Calculate early exit (if out_time < shift_end)
    if out_time and out_time.time() < shift_end_time:
        early_delta = datetime.combine(out_time.date(), shift_end_time) - \
                     datetime.combine(out_time.date(), out_time.time())
        early_minutes = round(early_delta.total_seconds() / 60)
        early_exit = format_minutes_to_hhmm(early_minutes)
    
    # Calculate overtime (if out_time > shift_end)
    if out_time and out_time.time() > shift_end_time:
        ot_delta = datetime.combine(out_time.date(), out_time.time()) - \
                  datetime.combine(out_time.date(), shift_end_time)
        ot_minutes = round(ot_delta.total_seconds() / 60)
        overtime = format_minutes_to_hhmm(ot_minutes)
    
    return late_entry, early_exit, overtime


def format_minutes_to_hhmm(minutes):
    """Format minutes to HH:MM format (e.g., "01:30" for 90 minutes)"""
    if minutes is None or minutes == 0:
        return "-"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    return f"{hours:02d}:{mins:02d}"


def get_status_with_color(status):
    """Get status with HTML color formatting"""
    colors = {
        "Present": "<span style='color: green'>Present</span>",
        "Absent": "<span style='color: red'>Absent</span>",
        "Half Day": "<span style='color: orange'>Half Day</span>",
        "On Leave": "<span style='color: blue'>Leave</span>",
        "Work From Home": "<span style='color: purple'>WFH</span>",
    }
    return colors.get(status, status)


def get_conditions(filters):
    conditions = ""
    
    if filters.get("employee"):
        conditions += " AND att.employee = %(employee)s"
    
    if filters.get("from_date"):
        conditions += " AND att.attendance_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND att.attendance_date <= %(to_date)s"
    
    return conditions


def get_columns():
    return [
        {
            "label": _("Reference"),
            "fieldname": "reference",
            "fieldtype": "Link",
            "options": "Attendance",
            "width": 120,
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
            "width": 150,
        },
        {
            "label": _("Date"),
            "fieldname": "attendance_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Check-in"),
            "fieldname": "check_in",
            "fieldtype": "Datetime",
            "width": 140,
        },
        {
            "label": _("Check-out"),
            "fieldname": "check_out",
            "fieldtype": "Datetime",
            "width": 140,
        },
        {
            "label": _("Late Entry"),
            "fieldname": "late_entry",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Early Exit"),
            "fieldname": "early_exit",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Overtime"),
            "fieldname": "overtime",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Working Hours"),
            "fieldname": "working_hours",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Shift Type"),
            "fieldname": "shift_type",
            "fieldtype": "Link",
            "options": "Shift Type",
            "width": 120,
        },
    ]