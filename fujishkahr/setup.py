import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from fujishkahr.custom.custom_field.employee import get_employee_custom_fields
from fujishkahr.custom.custom_field.holiday_list import get_holiday_list_custom_fields
from fujishkahr.custom.custom_field.leave_policy import get_leave_policy_custom_fields
from fujishkahr.custom.custom_field.branch import get_branch_custom_fields
from fujishkahr.custom.custom_field.company import get_company_custom_fields
from fujishkahr.custom.custom_field.shift_type import get_shift_type_custom_fields
from fujishkahr.custom.custom_field.leave_type import get_leave_type_custom_fields
from fujishkahr.custom.custom_field.user import get_user_custom_fields
from fujishkahr.custom.custom_field.employee_checkin import get_employee_checkin_custom_fields
from fujishkahr.custom.custom_field.salary_component import get_salary_component_custom_fields
from fujishkahr.custom.custom_field.employment_type import get_employment_type_custom_fields

def after_install():
	create_custom_fields(get_custom_fields(), ignore_validate=True)

def after_migrate():
	after_install()
	create_custom_roles(get_fujishkahr_roles())

def before_uninstall():
	delete_custom_fields(get_custom_fields())

def before_migrate():
	pass

def delete_custom_fields(custom_fields: dict):
	'''
		Method to Delete custom fields
		args:
			custom_fields: a dict like `{'Task': [{fieldname: 'your_fieldname', ...}]}`
	'''
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)
		frappe.clear_cache(doctype=doctype)

def get_custom_fields():
	'''
		Method to get all custom fields that need to be created for PW IT Helpdesk and CM
	'''
	custom_fields = get_employee_custom_fields()
	custom_fields.update(get_holiday_list_custom_fields())
	custom_fields.update(get_leave_policy_custom_fields())
	custom_fields.update(get_branch_custom_fields())
	custom_fields.update(get_company_custom_fields())
	custom_fields.update(get_shift_type_custom_fields())
	custom_fields.update(get_leave_type_custom_fields())
	custom_fields.update(get_user_custom_fields())
	custom_fields.update(get_employee_checkin_custom_fields())
	custom_fields.update(get_salary_component_custom_fields())
	custom_fields.update(get_employment_type_custom_fields())
	return custom_fields

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
	return ['Fujishka HR', 'Fujishka Employee', 'CEO']

