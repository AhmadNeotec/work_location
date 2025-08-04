import frappe
import time
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def add_employee_checkin_fields(max_retries=3, retry_delay=5):
    """
    Add custom fields to Employee Checkin doctype with retry logic for lock timeouts
    
    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay in seconds between retries
    """
    # Make sure Work Location exists
    if not frappe.db.exists("DocType", "Work Location"):
        frappe.throw("Work Location Doctype must be installed before adding custom fields.")

    custom_fields = {
        "Employee Checkin": [
            {
                "fieldname": "work_location",
                "label": "Work Location",
                "fieldtype": "Link",
                "options": "Work Location",
                "insert_after": "employee"
            },
            {
                "fieldname": "current_lat",
                "label": "Current Latitude",
                "fieldtype": "Float",
                "insert_after": "work_location"
            },
            {
                "fieldname": "current_lng",
                "label": "Current Longitude",
                "fieldtype": "Float",
                "insert_after": "current_lat"
            },
            {
                "fieldname": "is_remote",
                "label": "Is Remote",
                "fieldtype": "Check",
                "insert_after": "current_lng"
            }
        ]
    }

    # Retry logic for handling lock timeouts
    for attempt in range(max_retries):
        try:
            frappe.db.begin()  # Start transaction
            create_custom_fields(custom_fields)
            frappe.db.commit()  # Commit transaction
            print(f"Custom fields added successfully on attempt {attempt + 1}")
            return
            
        except frappe.QueryTimeoutError as e:
            frappe.db.rollback()  # Rollback on timeout
            if attempt < max_retries - 1:
                print(f"Lock timeout on attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                frappe.throw(f"Failed to add custom fields after {max_retries} attempts due to lock timeout: {str(e)}")
                
        except frappe.DuplicateEntryError:
            frappe.db.rollback()
            print("Custom fields already exist, skipping...")
            return
            
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(f"Error adding custom fields: {str(e)}")