import frappe
import subprocess
import os
import re
import json

DOMAIN = "uat.fujishkahrms.com"

def get_bench_path():
	return os.path.abspath(
		os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
	)

def get_bench_bin():
	"""Auto-detect bench binary — works on both local and production."""
	import shutil
	candidates = [
		shutil.which("bench"),
		os.path.expanduser("~/.local/bin/bench"),
		"/usr/local/bin/bench",
		"/home/frappe/.local/bin/bench",
	]
	for path in candidates:
		if path and os.path.exists(path):
			return path
	frappe.throw("bench binary not found.")

def get_mariadb_credentials():
	return "root", "fujishka!"

@frappe.whitelist()
def create_new_site(site_name, admin_password="admin"):
	"""
	Create a new Frappe site with all apps installed.

	API endpoint:
		POST /api/method/fujishkahr.api.site_creation.create_new_site

	Body:
		{
			"site_name": "testsite",
			"admin_password": "admin"
		}

	site_name auto-becomes: testsite.fujishkahrms.com.com
	"""

	if not frappe.has_permission("System Settings", "write"):
		frappe.throw("Only System Managers can create sites.", frappe.PermissionError)

	if not site_name or not site_name.strip():
		frappe.throw("site_name is required.")

	site_name = site_name.strip()

	if not re.match(r'^[a-zA-Z0-9\-]+$', site_name):
		frappe.throw("Invalid site name. Use only letters, numbers, hyphens.")

	if not admin_password or not admin_password.strip():
		frappe.throw("admin_password cannot be empty.")

	if not site_name.endswith(f".{DOMAIN}"):
		site_name = f"{site_name}.{DOMAIN}"

	bench_path           = get_bench_path()
	bench_bin            = get_bench_bin()
	db_username, db_pass = get_mariadb_credentials()

	commands = [
		{
			"label": "Creating site",
			"cmd": [
				bench_bin, "new-site", site_name,
				"--admin-password", admin_password,
				"--db-root-username", db_username,
				"--mariadb-root-password", db_pass,
				"--mariadb-user-host-login-scope=%",
			]
		},
		{
			"label": "Installing erpnext",
			"cmd": [bench_bin, "--site", site_name, "install-app", "erpnext"]
		},
		{
			"label": "Installing hrms",
			"cmd": [bench_bin, "--site", site_name, "install-app", "hrms"]
		},
		{
			"label": "Installing fujishkahr",
			"cmd": [bench_bin, "--site", site_name, "install-app", "fujishkahr"]
		},
	]

	logs = []

	for step in commands:
		result = subprocess.run(
			step["cmd"],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=600
		)

		logs.append({
			"step":       step["label"],
			"returncode": result.returncode,
			"stdout":     result.stdout[-1000:],
			"stderr":     result.stderr[-1000:],
		})

		if result.returncode != 0:
			return {
				"success":   False,
				"failed_at": step["label"],
				"logs":      logs,
			}

	return {
		"success": True,
		"site":    site_name,
		"url":     f"https://{site_name}",
		"logs":    logs,
	}


@frappe.whitelist()
def get_bench_bin_path():
	"""Safe test endpoint — confirms setup is correct."""
	bench_path = get_bench_path()
	bench_bin  = get_bench_bin()

	config_path = os.path.join(bench_path, 'sites', 'common_site_config.json')
	has_root_password = False
	db_username = None
	try:
		with open(config_path) as f:
			config = json.load(f)
		has_root_password = bool(config.get('root_password'))
		db_username = config.get('root_login', 'root')
	except Exception:
		pass

	return {
		"bench_bin":         bench_bin,
		"bench_bin_exists":  os.path.exists(bench_bin) if bench_bin else False,
		"bench_path":        bench_path,
		"has_root_password": has_root_password,
		"db_username":       db_username,
		"domain":            DOMAIN,
		"ready":             bool(bench_bin and os.path.exists(bench_bin) and has_root_password),
	}