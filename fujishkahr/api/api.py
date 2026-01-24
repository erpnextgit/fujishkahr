import frappe

@frappe.whitelist()
def set_user_language(lang):
	"""Set the language preference for the logged-in user."""
	if lang in ["en", "ar"]:
		frappe.db.set_value("User", frappe.session.user, "language", lang)
		frappe.clear_cache(user=frappe.session.user)
