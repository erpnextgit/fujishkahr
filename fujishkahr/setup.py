import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_migrate():
	create_custom_roles(get_fujishkahr_roles())

def before_migrate():
	pass

def create_custom_roles(roles):
	'''
		Method to create custom Role
		args:
			roles : Role List (list of string)
		example:
			["Site Engineer", "Drawing User"]
	'''
	for role in roles:
		if not frappe.db.exists("Role", role):
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role
			})
			role_doc.insert(ignore_permissions=True)
	frappe.db.commit()


def get_fujishkahr_roles():
	'''
		Method to get fujishkahr specific roles
	'''
	return ['Fujishka HR', 'Fujishka Employee']

