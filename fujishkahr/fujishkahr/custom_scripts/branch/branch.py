import frappe

def set_branch_name(doc, method):
	"""
	Set branch_unique_name before insert
	Format: "BranchName - CompanyAbbr"
	"""
	if doc.company:
		company_abbr = frappe.db.get_value(
			"Company", doc.company, "abbr"
		)

		if not company_abbr:
			frappe.throw(
				f"Company abbreviation not found for {doc.company}!"
			)

		existing = frappe.db.exists("Branch", {
			"branch_code": doc.branch_code,
			"company":     doc.company
		})

		if existing:
			frappe.throw(
				f"Branch Code <b>{doc.branch_code}</b> already "
				f"exists for company <b>{doc.company}</b>!"
			)

		doc.branch_unique_name = f"{doc.branch} - {company_abbr}"

	else:
		frappe.throw("Company is required!")