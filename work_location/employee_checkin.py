import frappe
from frappe import _

def validate_checkin_location(doc, method):
    """
    Validate that the selected custom_checkin_location is in the employee's custom_allowed_shift_locations.
    Set the shift field to the Shift Type from the Shift Assignment matching shift_location.
    Override geolocation validation if not required.
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
    frappe.log_error(
        message=f"Allowed shift locations for {doc.employee}: {allowed_locations}",
        title="Allowed Shift Locations Debug"
    )

    if not allowed_locations:
        frappe.throw(_("No valid Shift Locations defined for employee {0}.").format(doc.employee))

    # Validate custom_checkin_location is in allowed_locations
    if doc.custom_checkin_location not in allowed_locations:
        frappe.throw(_("Selected Checkin Location {0} is not in the employee's allowed locations: {1}").format(
            doc.custom_checkin_location, ", ".join(allowed_locations)
        ))

    # Fetch Shift Assignment to get Shift Type
    shift_assignment_all = frappe.get_all(
        "Shift Assignment",
        filters={
            "employee": doc.employee,
            "start_date": ["<=", frappe.utils.getdate(doc.time)],
            "docstatus": 1,
            "shift_location": doc.custom_checkin_location,
        },
        fields=["shift_type", "shift_location", "name", "start_date", "end_date"],
    )

    # Filter manually
    shift_assignment = None
    for sa in shift_assignment_all:
        if not sa.end_date or sa.end_date >= frappe.utils.getdate(doc.time):
            shift_assignment = sa
            break

    if shift_assignment:
        doc.shift = shift_assignment["shift_type"]
        frappe.log_error(
            message=f"Set shift to {doc.shift} for {doc.employee}",
            title="Shift Type Debug"
        )
    else:
        doc.shift = "Day"  # Default fallback
        frappe.log_error(
            message=f"No valid Shift Assignment found for employee {doc.employee} at time {doc.time}. Using default shift 'Day'.",
            title="No Shift Assignment"
        )


    # Bypass geolocation validation if not required
    if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
        frappe.log_error(
            message=f"Geolocation tracking disabled, bypassing validation for {doc.employee}",
            title="Geolocation Debug"
        )
        return

    # Validate geolocation if enabled and coordinates are provided
    if doc.latitude and doc.longitude:
        shift_location = frappe.get_doc("Shift Location", doc.custom_checkin_location)
        if shift_location.latitude and shift_location.longitude and shift_location.checkin_radius:
            distance = ((float(doc.latitude) - float(shift_location.latitude)) ** 2 +
                        (float(doc.longitude) - float(shift_location.longitude)) ** 2) ** 0.5 * 111320
            frappe.log_error(
                message=f"Geolocation check for {doc.custom_checkin_location}: distance={distance}, radius={shift_location.checkin_radius}",
                title="Geolocation Debug"
            )
            if distance > shift_location.checkin_radius:
                frappe.throw(_(
                    "Check-in is {0} meters from {1}, exceeding the allowed radius of {2} meters."
                ).format(distance, doc.custom_checkin_location, shift_location.checkin_radius))
    else:
        frappe.log_error(
            message=f"Employee {doc.employee} checked in at {doc.custom_checkin_location} without geolocation data.",
            title="Missing Geolocation"
        )