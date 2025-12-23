# work_location/overrides/shift_assignment_override.py
import frappe
from hrms.hr.doctype.shift_assignment.shift_assignment import ShiftAssignment

class CustomShiftAssignment(ShiftAssignment):
    def validate_overlapping_shifts(self):
        overlapping = frappe.db.sql("""
            select name, shift_type, shift_location, start_date, end_date
            from `tabShift Assignment`
            where employee = %s
            and docstatus < 2
            and shift_location = %s
            and shift_type = %s
            and (
                (start_date <= %s and end_date >= %s)
                or (start_date <= %s and end_date >= %s)
                or (start_date >= %s and end_date <= %s)
            )
            and name != %s
        """, (
            self.employee, self.shift_location, self.shift_type,
            self.end_date, self.start_date,
            self.start_date, self.end_date,
            self.start_date, self.end_date,
            self.name
        ), as_dict=True)

        for d in overlapping:
                # throw only if BOTH location and shift type are same
                if d.shift_location == self.shift_location and d.shift_type == self.shift_type:
                    self.throw_overlap_error(d)
