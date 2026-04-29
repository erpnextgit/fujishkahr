import frappe

def execute():
	"""
	Change Branch DocType autoname to use
	branch_unique_name field
	"""
	frappe.db.set_value(
		"DocType",
		"Branch",
		"autoname",
		"field:branch_unique_name"
	)

	frappe.clear_cache(doctype="Branch")
	frappe.db.commit()