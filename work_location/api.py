# Add this to your work_location app (e.g., work_location/work_location/api.py)

import frappe

@frappe.whitelist()
def get_work_location_coordinates(work_location_name):
    """
    Get coordinates for a specific work location
    """
    try:
        work_location = frappe.get_doc("Work Location", work_location_name)
        
        if not work_location.latitude or not work_location.longitude:
            frappe.throw("Work Location does not have coordinates configured")
            
        return {
            "latitude": work_location.latitude,
            "longitude": work_location.longitude,
            "radius": work_location.radius or 0,
            "name": work_location.name
        }
        
    except frappe.DoesNotExistError:
        frappe.throw("Work Location not found")
    except Exception as e:
        frappe.log_error(f"Error fetching work location coordinates: {str(e)}")
        frappe.throw("Error fetching work location details")