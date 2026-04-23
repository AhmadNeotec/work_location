# Copyright (c) 2026, Neotec and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, format_datetime, time_diff_in_seconds
from datetime import timedelta
from hrms.hr.utils import get_distance_between_coordinates

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data, None, None

def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
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
            "label": _("Location"),
            "fieldname": "location",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Check-in Status"),
            "fieldname": "checkin_status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Check-in Time"),
            "fieldname": "checkin_time",
            "fieldtype": "Datetime",
            "width": 150,
        },
        {
            "label": _("Check-out Time"),
            "fieldname": "checkout_time",
            "fieldtype": "Datetime",
            "width": 150,
        },
        {
            "label": _("Duration"),
            "fieldname": "duration",
            "fieldtype": "Data",
            "width": 150,
        },
    ]

def get_data(filters):
    # Get all office locations
    location_filters = {"latitude": ["is", "set"], "longitude": ["is", "set"]}
    if filters.get("locations"):
        location_filters["name"] = filters.get("locations")

    all_locations = frappe.get_all(
        "Shift Location",
        fields=["name", "location_name", "latitude", "longitude"],
        filters=location_filters
    )
    
    # Build location map
    location_map = {loc.name: loc for loc in all_locations}
    
    # Get employee checkins based on filters
    checkin_filters = {}
    if filters.get("employee"):
        checkin_filters["employee"] = filters.get("employee")
    if filters.get("from_date") and filters.get("to_date"):
        checkin_filters["time"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
    
    checkins = frappe.get_all(
        "Employee Checkin",
        fields=["name", "employee", "employee_name", "log_type", "time", 
                "custom_checkin_location", "latitude", "longitude"],
        filters=checkin_filters,
        order_by="employee, time"
    )
    
    # Process checkins to create location attendance data
    data = []
    employee_checkins = {}
    
    # Group checkins by employee and date
    for checkin in checkins:
        checkin_date = getdate(checkin.time).strftime("%Y-%m-%d")
        key = f"{checkin.employee}_{checkin_date}"
        
        if key not in employee_checkins:
            employee_checkins[key] = {
                "employee": checkin.employee,
                "employee_name": checkin.employee_name,
                "date": checkin_date,
                "locations": {}
            }
        
        location_name = checkin.custom_checkin_location or "Unknown"
        
        if location_name not in employee_checkins[key]["locations"]:
            employee_checkins[key]["locations"][location_name] = {
                "checkin": None,
                "checkout": None,
                "location_name": location_map.get(location_name, {}).get("location_name", location_name),
                "latitude": checkin.latitude,
                "longitude": checkin.longitude,
                "location_coords": (
                    location_map.get(location_name, {}).get("latitude"),
                    location_map.get(location_name, {}).get("longitude")
                )
            }
        
        if checkin.log_type == "IN":
            employee_checkins[key]["locations"][location_name]["checkin"] = checkin.time
        elif checkin.log_type == "OUT":
            employee_checkins[key]["locations"][location_name]["checkout"] = checkin.time
    
    # Convert to report data format
    for key, emp_data in employee_checkins.items():
        for loc_name, loc_data in emp_data["locations"].items():
            # Calculate distance
            distance = "N/A"
            if loc_data["latitude"] and loc_data["longitude"] and loc_data["location_coords"][0]:
                try:
                    dist = get_distance_between_coordinates(
                        loc_data["location_coords"][0],
                        loc_data["location_coords"][1],
                        loc_data["latitude"],
                        loc_data["longitude"]
                    )
                    distance = f"{int(dist)} meters"
                except:
                    distance = "N/A"
            
            # Format location name with distance
            location_display = f"{loc_data['location_name']} ({distance})"
            
            # Calculate duration
            duration = "N/A"
            if loc_data["checkin"] and loc_data["checkout"]:
                try:
                    time_diff = time_diff_in_seconds(loc_data["checkout"], loc_data["checkin"])
                    hours = int(time_diff // 3600)
                    minutes = int((time_diff % 3600) // 60)
                    duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
                except:
                    duration = "N/A"
            
            # Determine check-in status
            if loc_data["checkin"] and loc_data["checkout"]:
                status = "Complete"
            elif loc_data["checkin"]:
                status = "Checked In"
            else:
                status = "Not Checked In"
            
            data.append({
                "date": emp_data["date"],
                "employee": emp_data["employee"],
                "employee_name": emp_data["employee_name"],
                "location": location_display,
                "checkin_status": status,
                "checkin_time": loc_data["checkin"],
                "checkout_time": loc_data["checkout"],
                "duration": duration
            })
    
    # Add all office locations that weren't visited
    if filters.get("show_all_locations"):
        for loc in all_locations:
            # Check if this location appears in data
            found = False
            for row in data:
                if loc.location_name in row.get("location", ""):
                    found = True
                    break
            
            if not found:
                data.append({
                    "date": filters.get("from_date") or getdate().strftime("%Y-%m-%d"),
                    "employee": filters.get("employee") or "",
                    "employee_name": "",
                    "location": f"{loc.location_name} (Not Visited)",
                    "checkin_status": "Not Visited",
                    "checkin_time": None,
                    "checkout_time": None,
                    "duration": "N/A"
                })
    
    return data