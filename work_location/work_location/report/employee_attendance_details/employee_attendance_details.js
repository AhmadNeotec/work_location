// Copyright (c) 2026, Neotec and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Attendance details"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "present",
			"label": __("Present"),
			"fieldtype": "Check",
			"default": 1  // Checked by default
		},
		{
			"fieldname": "absent",
			"label": __("Absent"),
			"fieldtype": "Check",
			"default": 0  // Not checked by default
		},
		{
			"fieldname": "shift_type",
			"label": __("Shift Type"),
			"fieldtype": "Link",
			"options": "Shift Type",
			"reqd": 0  // Optional filter
		}
	],


	"formatter": function (value, row, column, data) {
		if (column.fieldname === "present" && value === "P") {
			return `<span style='color: darkgreen'>${value}</span>`;
		} else if (column.fieldname === "present" && value === "A") {
			return `<span style='color: darkred'>${value}</span>`;
		}
		return value;
	}
};
