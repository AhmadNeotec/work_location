import frappe
from hrms.hr.doctype.shift_assignment.shift_assignment import ShiftAssignment

def custom_validate_overlapping_shifts(self):
    # allow multiple shift assignments as long as shift_location is different
    overlapping = frappe.db.sql("""
        select name, shift_type, shift_location, start_date, end_date
        from `tabShift Assignment`
        where employee = %s
        and docstatus < 2
        and (
            (start_date <= %s and end_date >= %s)
            or (start_date <= %s and end_date >= %s)
            or (start_date >= %s and end_date <= %s)
        )
        and name != %s
    """, (self.employee, self.end_date, self.start_date,
          self.start_date, self.end_date,
          self.start_date, self.end_date,
          self.name), as_dict=True)

    for d in overlapping:
        # only throw if same location
        if d.shift_location == self.shift_location:
            self.throw_overlap_error(d)

# Patch the method
ShiftAssignment.validate_overlapping_shifts = custom_validate_overlapping_shifts
