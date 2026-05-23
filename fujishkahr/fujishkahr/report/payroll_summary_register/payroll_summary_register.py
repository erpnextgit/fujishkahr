# Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")

def execute(filters=None):
	"""
	Main entry point. Fetches salary slips and builds report rows
	based on selected filters and report type.
	"""
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	report_type = filters.get("report_type") or "Full Report"

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips)
	columns = get_columns(earning_types, ded_types, report_type)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")

	data = []
	for ss in salary_slips:
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"branch": ss.branch,
			"department": ss.department,
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"absent_days": ss.absent_days,
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
		}

		update_column_width(ss, columns)

		if report_type in ("Full Report", "Salary Only"):
			for e in earning_types:
				row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

			for d in ded_types:
				row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)
		else:
			row.update(
				{
					"gross_pay": ss.gross_pay,
					"total_deduction": flt(ss.total_deduction),
					"net_pay": ss.net_pay,
				}
			)

		employee_pf = 0
		employee_esi = 0

		slip_doc = frappe.get_doc("Salary Slip", ss.name)

		for d in slip_doc.deductions:
			component = frappe.get_cached_doc("Salary Component", d.salary_component)

			if component.is_employee_pf:
				employee_pf += flt(d.amount)

			if component.is_employee_esi:
				employee_esi += flt(d.amount)

		employer_pf = employee_pf

		employer_esi = (
			flt(slip_doc.gross_pay) * 0.0325
			if flt(slip_doc.gross_pay) <= 21000
			else 0
		)

		if report_type in ("Full Report", "PF Only", "Employer Contribution Only"):
			row["employee_pf"] = employee_pf
			row["employer_pf"] = employer_pf
			row["total_pf"] = employee_pf + employer_pf

		if report_type in ("Full Report", "ESI Only", "Employer Contribution Only"):
			row["employee_esi"] = employee_esi
			row["employer_esi"] = employer_esi
			row["total_esi"] = employee_esi + employer_esi

		if report_type in ("Full Report", "Employer Contribution Only", "PF Only", "ESI Only"):
			row["employer_contribution_total"] = employer_pf + employer_esi

		if report_type in ("Full Report", "Employer Contribution Only", "PF Only", "ESI Only"):
			row["total_statutory_deduction"] = employee_pf + employee_esi + employer_pf + employer_esi

		data.append(row)

	return columns, data

def get_columns(earning_types, ded_types, report_type="Full Report"):
	"""
	Builds and returns column definitions based on the selected report type.
	"""

	identity_columns = [
		{
			"label": _("Salary Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": -1,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": -1,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Payment Days"),
			"fieldname": "payment_days",
			"fieldtype": "Float",
			"width": 120,
		},
	]

	attendance_columns = [
		{
			"label": _("Leave Without Pay"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Float",
			"width": 50,
		},
		{
			"label": _("Absent Days"),
			"fieldname": "absent_days",
			"fieldtype": "Float",
			"width": 50,
		},
	]

	earning_columns = [
		{
			"label": earning,
			"fieldname": frappe.scrub(earning),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
		for earning in earning_types
	]

	gross_pay_column = [
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	]

	deduction_columns = [
		{
			"label": deduction,
			"fieldname": frappe.scrub(deduction),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
		for deduction in ded_types
	]

	salary_summary_columns = [
		{
			"label": _("Total Deduction"),
			"fieldname": "total_deduction",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Net Pay"),
			"fieldname": "net_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]

	pf_columns = [
		{
			"label": _("Employee PF"),
			"fieldname": "employee_pf",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Employer PF"),
			"fieldname": "employer_pf",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total PF"),
			"fieldname": "total_pf",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]

	esi_columns = [
		{
			"label": _("Employee ESI"),
			"fieldname": "employee_esi",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Employer ESI"),
			"fieldname": "employer_esi",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total ESI"),
			"fieldname": "total_esi",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]

	employer_contribution_total_column = [
		{
			"label": _("Employer Contribution Total"),
			"fieldname": "employer_contribution_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 180,
		}
	]

	total_statutory_deduction_column = [
		{
			"label": _("Total Statutory Deduction"),
			"fieldname": "total_statutory_deduction",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 180,
		}
	]

	currency_column = [
		{
			"label": _("Currency"),
			"fieldtype": "Data",
			"fieldname": "currency",
			"options": "Currency",
			"hidden": 1,
		}
	]

	if report_type == "PF Only":
		return (
			identity_columns
			+ pf_columns
			+ employer_contribution_total_column
			+ total_statutory_deduction_column
			+ currency_column
		)

	elif report_type == "ESI Only":
		return (
			identity_columns
			+ gross_pay_column
			+ esi_columns
			+ employer_contribution_total_column
			+ total_statutory_deduction_column
			+ currency_column
		)

	elif report_type == "Employer Contribution Only":
		return (
			identity_columns
			+ gross_pay_column
			+ [pf_columns[1]]
			+ [esi_columns[1]]
			+ [pf_columns[2]]
			+ [esi_columns[2]]
			+ employer_contribution_total_column
			+ total_statutory_deduction_column
			+ currency_column
		)

	elif report_type == "Salary Only":
		return (
			identity_columns
			+ attendance_columns
			+ earning_columns
			+ gross_pay_column
			+ deduction_columns
			+ salary_summary_columns
			+ currency_column
		)

	else:
		return (
			identity_columns
			+ attendance_columns
			+ earning_columns
			+ gross_pay_column
			+ deduction_columns
			+ salary_summary_columns
			+ [pf_columns[1], pf_columns[2]]
			+ [esi_columns[1], esi_columns[2]]
			+ employer_contribution_total_column
			+ total_statutory_deduction_column
			+ currency_column
		)

def get_earning_and_deduction_types(salary_slips):
	"""
	Returns sorted lists of earning and deduction component names
	used across the given salary slips
	"""
	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}

	for salary_component in get_salary_components(salary_slips):
		component_type = get_salary_component_type(salary_component)
		salary_component_and_type[_(component_type)].append(salary_component)

	return (
		sorted(salary_component_and_type[_("Earning")]),
		sorted(salary_component_and_type[_("Deduction")]),
	)

def update_column_width(ss, columns):
	"""
	Expands column width to 120 for Branch, Department, Designation,
	and LWP if data is present.
	"""
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		lwp_col = next((c for c in columns if c.get("fieldname") == "leave_without_pay"), None)
		if lwp_col:
			lwp_col.update({"width": 120})

def get_salary_components(salary_slips):
	"""
	Returns distinct salary component names with
	non-zero amounts across the given salary slips.
	"""
	return (
		frappe.qb.from_(salary_detail)
		.where(
			(salary_detail.amount != 0)
			& (salary_detail.parent.isin([d.name for d in salary_slips]))
		)
		.select(salary_detail.salary_component)
		.distinct()
	).run(pluck=True)

def get_salary_component_type(salary_component):
	"""
	Returns whether a salary component is an Earning or Deduction.
	"""
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)

def get_salary_slips(filters, company_currency):
	"""
	Fetches all salary slips matching the given filters
	(date, company, employee, department, etc.).
	"""
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	query = frappe.qb.from_(salary_slip).select(salary_slip.star)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))

	if filters.get("department"):
		query = query.where(salary_slip.department == filters["department"])

	if filters.get("designation"):
		query = query.where(salary_slip.designation == filters["designation"])

	if filters.get("branch"):
		query = query.where(salary_slip.branch == filters["branch"])

	salary_slips = query.run(as_dict=1)

	return salary_slips or []

def get_employee_doj_map():
	"""
	Returns a dict mapping employee name to date of joining.
	"""
	employee = frappe.qb.DocType("Employee")

	result = (
		frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)
	).run()

	return frappe._dict(result)

def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	"""
	Fetches earning or deduction amounts per slip and
	returns them as a nested dict {slip: {component: amount}}.
	"""
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where(
			(salary_detail.parent.isin(salary_slips))
			& (salary_detail.parentfield == component_type)
		)
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
