import frappe
from frappe import _

def validate_checkin_location(doc, method):
    """
    Validate that the selected custom_checkin_location is in the employee's custom_allowed_shift_locations.
    Override default geolocation validation if not required.
    """
    if not doc.custom_checkin_location:
        frappe.throw(_("Checkin Location is mandatory."))
    if not doc.log_type:
        frappe.throw(_("Log Type (IN/OUT) is mandatory."))

    # Get the employee's allowed shift locations
    employee = frappe.get_doc("Employee", doc.employee)
    allowed_locations = employee.get("custom_allowed_shift_locations") or []
    if allowed_locations is None:
        allowed_locations = []
        frappe.log_error(
            message=f"Employee {doc.employee} has no custom_allowed_shift_locations defined or it is set to None.",
            title="Invalid Allowed Shift Locations"
        )
    allowed_locations = [row.shift_location for row in allowed_locations if row.shift_location]

    if not allowed_locations:
        frappe.throw(_("No valid Shift Locations defined for employee {0}. Please add locations in the Employee record.").format(doc.employee))

    # Validate custom_checkin_location is in allowed_locations
    if doc.custom_checkin_location not in allowed_locations:
        frappe.throw(_("Selected Checkin Location {0} is not in the employee's allowed locations: {1}").format(
            doc.custom_checkin_location, ", ".join(allowed_locations)
        ))

    # Bypass geolocation validation if not required
    if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
        doc.shift = doc.custom_checkin_location
        return

    # Validate geolocation if enabled and coordinates are provided
    if doc.latitude and doc.longitude:
        shift_location = frappe.get_doc("Shift Location", doc.custom_checkin_location)
        if shift_location.latitude and shift_location.longitude and shift_location.checkin_radius:
            distance = ((float(doc.latitude) - float(shift_location.latitude)) ** 2 +
                        (float(doc.longitude) - float(shift_location.longitude)) ** 2) ** 0.5 * 111320  # Convert to meters
            if distance > shift_location.checkin_radius:
                frappe.throw(_(
                    "Check-in is {0} meters from {1}, exceeding the allowed radius of {2} meters."
                ).format(distance, doc.custom_checkin_location, shift_location.checkin_radius))
    else:
        # Log missing geolocation data but allow check-in
        frappe.log_error(
            message=f"Employee {doc.employee} checked in at {doc.custom_checkin_location} without geolocation data.",
            title="Missing Geolocation"
        )

    # Override Shift Assignment's Shift Location for attendance processing
    shift_assignment = frappe.get_all(
        "Shift Assignment",
        filters={
            "employee": doc.employee,
            "start_date": ["<=", doc.time],
            "end_date": [">=", doc.time],
            "docstatus": 1
        },
        fields=["shift_location"],
        limit=1
    )

    if shift_assignment and shift_assignment[0].shift_location != doc.custom_checkin_location:
        frappe.log_error(
            message=f"Employee {doc.employee} checked in at {doc.custom_checkin_location} instead of assigned {shift_assignment[0].shift_location}",
            title="Shift Location Override"
        )
        doc.shift = doc.custom_checkin_location
        
        