// Copyright (c) 2026, Neotec and contributors
// For license information, please see license.txt

frappe.query_reports["Employee check-in & check-out Details"] = {
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
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Link",
			options: "Shift Type",
		},
		{
			fieldname: "log_type",
			label: __("Log Type"),
			fieldtype: "Select",
			options: ["", "IN", "OUT"],
		},
	],
};
