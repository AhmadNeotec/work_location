// Copyright (c) 2026, Neotec and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Time tracker"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(frappe.datetime.get_today()),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "hr_format",
			label: __("HR Format"),
			fieldtype: "Select",
			options: "\n24 hr\n12 hr",
			default: "24 hr",
			reqd: 1,
		},
	],
};
