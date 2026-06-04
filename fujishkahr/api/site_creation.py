import frappe
import subprocess
import os
import re
import json


def get_bench_path():
	return os.path.abspath(
		os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
	)


def get_bench_bin():
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


def get_mariadb_password():
	return "zHhdMoE1bzD4EbWV"


@frappe.whitelist()
def create_new_site(site_name, admin_password="admin"):
	if not frappe.has_permission("System Settings", "write"):
		frappe.throw("Only System Managers can create sites.", frappe.PermissionError)

	if not site_name or not site_name.strip():
		frappe.throw("site_name is required.")

	site_name = site_name.strip()

	if not re.match(r'^[a-zA-Z0-9.\-]+$', site_name):
		frappe.throw("Invalid site name. Use only letters, numbers, dots, hyphens.")

	if not admin_password or not admin_password.strip():
		frappe.throw("admin_password cannot be empty.")

	bench_path   = get_bench_path()
	bench_bin    = get_bench_bin()
	mariadb_pass = get_mariadb_password()

	commands = [
		{
			"label": "Creating site",
			"cmd": [
				bench_bin, "new-site", site_name,
				"--admin-password", admin_password,
				"--mariadb-root-password", mariadb_pass,
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
	bench_path = get_bench_path()
	bench_bin  = get_bench_bin()
	return {
		"bench_bin":        bench_bin,
		"bench_bin_exists": os.path.exists(bench_bin) if bench_bin else False,
		"bench_path":       bench_path,
		"has_root_password": True,
		"ready":            bool(bench_bin and os.path.exists(bench_bin)),
	}