import frappe
import subprocess
import os
import re
import json
import shutil

DOMAIN = "uat.fujishkahrms.com"
CACHE_TTL = 60 * 60 * 24


def get_bench_path():
	return os.path.abspath(
		os.path.join(
			os.path.dirname(__file__),
			"..",
			"..",
			"..",
			".."
		)
	)


def get_bench_bin():

	candidates = [
		shutil.which("bench"),
		os.path.expanduser("~/.local/bin/bench"),
		"/usr/local/bin/bench",
		"/home/frappe/.local/bin/bench",
	]

	for path in candidates:
		if path and os.path.exists(path):
			return path

	frappe.throw("bench binary not found")


def get_mariadb_credentials():
	return "root", "fujishka!"


def validate_site_name(site_name):

	if not site_name:
		frappe.throw("site_name required")

	site_name = site_name.strip()

	if not re.match(
		r"^[a-zA-Z0-9\-]+$",
		site_name
	):
		frappe.throw(
			"Only letters numbers hyphens allowed"
		)

	if not site_name.endswith(
		f".{DOMAIN}"
	):
		site_name = (
			f"{site_name}.{DOMAIN}"
		)

	return site_name


def cache_key(site_name):
	return f"site_creation:{site_name}"


def save_status(site_name, data):

	frappe.cache().set_value(
		cache_key(site_name),
		data,
		expires_in_sec=CACHE_TTL
	)


def get_status(site_name):

	return (
		frappe.cache()
		.get_value(
			cache_key(site_name)
		)
	)


@frappe.whitelist()
def create_new_site(
	site_name,
	admin_password="admin"
):

	if "System Manager" not in frappe.get_roles():
		frappe.throw(
			"Only System Managers can create sites"
		)

	site_name = validate_site_name(
		site_name
	)

	existing = get_status(site_name)

	if (
		existing
		and existing.get("status")
		in (
			"queued",
			"running"
		)
	):
		return {
			"success": False,
			"message": "Site creation already running"
		}

	save_status(
		site_name,
		{
			"status": "queued",
			"progress": 0
		}
	)

	frappe.enqueue(
		method="fujishkahr.api.site_creation.create_site_job",
		queue="long",
		timeout=7200,
		enqueue_after_commit=True,
		site_name=site_name,
		admin_password=admin_password
	)

	return {
		"success": True,
		"site": site_name,
		"message": "Site creation started"
	}


@frappe.whitelist()
def get_site_creation_status(
	site_name
):

	site_name = validate_site_name(
		site_name
	)

	return (
		get_status(site_name)
		or
		{
			"status": "not_found"
		}
	)


def create_site_job(
	site_name,
	admin_password="admin"
):

	logs = []

	try:

		bench_path = get_bench_path()

		bench_bin = get_bench_bin()

		db_user, db_pass = (
			get_mariadb_credentials()
		)

		if os.path.exists(
			os.path.join(
				bench_path,
				"sites",
				site_name
			)
		):

			save_status(
				site_name,
				{
					"status": "failed",
					"error": "Site already exists"
				}
			)

			return

		commands = [

			(
				"Creating site",
				[
					bench_bin,
					"new-site",
					site_name,
					"--admin-password",
					admin_password,
					"--db-root-username",
					db_user,
					"--mariadb-root-password",
					db_pass,
					"--mariadb-user-host-login-scope=%"
				]
			),

			(
				"Installing ERPNext",
				[
					bench_bin,
					"--site",
					site_name,
					"install-app",
					"erpnext"
				]
			),

			(
				"Installing HRMS",
				[
					bench_bin,
					"--site",
					site_name,
					"install-app",
					"hrms"
				]
			),

			(
				"Installing Fujishkahr",
				[
					bench_bin,
					"--site",
					site_name,
					"install-app",
					"fujishkahr"
				]
			)

		]

		total = len(commands)

		for index, (
			label,
			cmd
		) in enumerate(
			commands,
			start=1
		):

			save_status(
				site_name,
				{
					"status": "running",
					"current_step": label,
					"completed_steps": (
						index - 1
					),
					"total_steps": total,
					"progress": round(
						(
							(index - 1)
							/
							total
						)
						*
						100
					),
					"recent_logs": [
						{
							"step": x["step"],
							"returncode": x["returncode"]
						}
						for x in logs[-3:]
					]
				}
			)

			result = subprocess.run(
				cmd,
				cwd=bench_path,
				capture_output=True,
				text=True,
				timeout=7200
			)

			logs.append({
				"step": label,
				"returncode": (
					result.returncode
				),
				"stdout": (
					result.stdout[-1000:]
				),
				"stderr": (
					result.stderr[-1000:]
				)
			})

			if result.returncode:

				try:

					subprocess.run(
						[
							bench_bin,
							"drop-site",
							site_name,
							"--force"
						],
						cwd=bench_path
					)

				except Exception:
					pass

				save_status(
					site_name,
					{
						"status": "failed",
						"failed_at": label,
						"progress": round(
							(
								(index - 1)
								/
								total
							)
							*
							100
						),
						"error": (
							result.stderr[-500:]
							or
							result.stdout[-500:]
						),
						"logs": logs[-3:]
					}
				)

				return

		save_status(
			site_name,
			{
				"status": "completed",
				"current_step": "Finished",
				"completed_steps": total,
				"total_steps": total,
				"progress": 100,
				"url": (
					f"https://{site_name}"
				),
				"summary": [
					{
						"step": x["step"],
						"returncode": (
							x["returncode"]
						)
					}
					for x in logs
				]
			}
		)

	except subprocess.TimeoutExpired:

		save_status(
			site_name,
			{
				"status": "failed",
				"error": "Timed out"
			}
		)

	except Exception:

		error = (
			frappe.get_traceback()
		)

		frappe.log_error(
			error,
			"Site Creation Failed"
		)

		save_status(
			site_name,
			{
				"status": "failed",
				"error": error
			}
		)


@frappe.whitelist()
def get_bench_bin_path():

	bench = get_bench_bin()

	return {
		"bench_bin": bench,
		"exists": os.path.exists(
			bench
		),
		"bench_path": get_bench_path(),
		"domain": DOMAIN
	}

