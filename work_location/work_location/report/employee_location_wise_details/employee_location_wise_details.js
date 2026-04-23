// Copyright (c) 2026, Neotec and contributors
// For license information, please see license.txt

frappe.query_reports["Employee location wise Details"] = {
	"filters": [
		{
			fieldname: "employee",
			label: "Employee",
			fieldtype: "Link",
			options: "Employee"
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date"
		},
		{
			fieldname: "locations",
			label: "Locations",
			fieldtype: "Link",
			options: "Shift Location"
		},
		{
			fieldname: "show_all_locations",
			label: "Show All Locations",
			fieldtype: "Check",
			default: 0
		}
	]
};
