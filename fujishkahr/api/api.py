import frappe

@frappe.whitelist()
def set_user_language(lang):
	"""Set the language preference for the logged-in user."""
	if lang in ["en", "ar"]:
		frappe.db.set_value("User", frappe.session.user, "language", lang)
		frappe.clear_cache(user=frappe.session.user)

@frappe.whitelist()
def get_employee_attendance_heatmap(employee, year):
	"""Get attendance data for an employee for a given year to render a heatmap."""
	data = {}

	attendance = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [f"{year}-01-01", f"{year}-12-31"]]
		},
		fields=[
			"attendance_date",
			"status",
			"late_entry",
			"early_exit"
		]
	)

	for row in attendance:
		date = row.attendance_date.strftime("%Y-%m-%d")

		if row.status == "Absent":
			data[date] = "absent"

		elif row.status == "On Leave":
			data[date] = "leave"

		elif row.status == "Work From Home":
			data[date] = "wfh"

		elif row.status == "Half Day":
			data[date] = "half_day"

		elif row.late_entry or row.early_exit:
			data[date] = "late_early"

		else:
			data[date] = "present"

	return data

import frappe
import json
import requests
from werkzeug.wrappers import Response
from urllib.parse import urlencode
import re

@frappe.whitelist()
def get_fb_login_url():
	app_id = frappe.conf.get("fb_app_id")
	redirect_uri = frappe.conf.get("fb_redirect_uri")

	params = {
		"client_id": app_id,
		"redirect_uri": redirect_uri,
		"scope": ",".join([
			"leads_retrieval",
			"pages_show_list",
			"pages_read_engagement",
			"pages_manage_ads",
			"pages_manage_metadata"
		]),
		"response_type": "code",
		"state": frappe.generate_hash(length=16)
	}

	login_url = "https://www.facebook.com/v25.0/dialog/oauth?" + urlencode(params)
	return {"login_url": login_url}


@frappe.whitelist(allow_guest=True)
def fb_callback(**kwargs):
	code = frappe.request.args.get("code")
	error = frappe.request.args.get("error")

	if error:
		frappe.log_error(f"FB OAuth error: {error}", "FB Login Error")
		return Response(
			"<script>window.location='/fb-lead-sync?error=access_denied'</script>",
			status=200,
			mimetype="text/html"
		)

	if not code:
		return Response(
			"<script>window.location='/fb-lead-sync?error=no_code'</script>",
			status=200,
			mimetype="text/html"
		)

	app_id = frappe.conf.get("fb_app_id")
	app_secret = frappe.conf.get("fb_app_secret")
	redirect_uri = frappe.conf.get("fb_redirect_uri")

	token_resp = requests.get(
		"https://graph.facebook.com/v25.0/oauth/access_token",
		params={
			"client_id": app_id,
			"client_secret": app_secret,
			"redirect_uri": redirect_uri,
			"code": code
		}
	)
	token_data = token_resp.json()

	if "error" in token_data:
		frappe.log_error(str(token_data), "FB Token Exchange Error")
		return Response(
			"<script>window.location='/fb-lead-sync?error=token_failed'</script>",
			status=200,
			mimetype="text/html"
		)

	short_token = token_data.get("access_token")

	long_token_resp = requests.get(
		"https://graph.facebook.com/v25.0/oauth/access_token",
		params={
			"grant_type": "fb_exchange_token",
			"client_id": app_id,
			"client_secret": app_secret,
			"fb_exchange_token": short_token
		}
	)
	long_token_data = long_token_resp.json()
	long_token = long_token_data.get("access_token", short_token)

	user_resp = requests.get(
		"https://graph.facebook.com/v25.0/me",
		params={"access_token": long_token, "fields": "id,name,email"}
	)
	user_data = user_resp.json()
	fb_user_id = user_data.get("id")

	save_fb_connection(fb_user_id, long_token, user_data.get("name"))

	return Response(
		f"<script>window.location='/fb-lead-sync?connected=1&fb_user={fb_user_id}'</script>",
		status=200,
		mimetype="text/html"
	)


@frappe.whitelist()
def get_fb_pages():
	connection = frappe.db.get_value(
		"FB Connection",
		{"erpnext_user": frappe.session.user, "is_active": 1},
		["user_access_token", "fb_user_id"],
		as_dict=True
	)

	if not connection:
		frappe.throw("Facebook account not connected. Please login with Facebook first.")

	resp = requests.get(
		"https://graph.facebook.com/v25.0/me/accounts",
		params={
			"access_token": connection.user_access_token,
			"fields": "id,name,access_token,picture,fan_count"
		}
	)
	pages_data = resp.json()

	if "error" in pages_data:
		frappe.throw(f"Facebook API Error: {pages_data['error'].get('message')}")

	pages = pages_data.get("data", [])

	result = []
	for page in pages:
		forms_resp = requests.get(
			f"https://graph.facebook.com/v25.0/{page['id']}/leadgen_forms",
			params={
				"access_token": page["access_token"],
				"fields": "id,name,status,leads_count,created_time"
			}
		)
		forms_data = forms_resp.json()
		page["lead_forms"] = forms_data.get("data", [])
		result.append(page)

	return result


@frappe.whitelist()
def save_page_config(page_id, page_name, page_access_token, form_ids="[]"):
	long_page_token_resp = requests.get(
		f"https://graph.facebook.com/v25.0/{page_id}",
		params={
			"fields": "access_token",
			"access_token": page_access_token
		}
	)
	long_page_token_data = long_page_token_resp.json()
	final_token = long_page_token_data.get("access_token", page_access_token)

	if frappe.db.exists("FB Page Config", {"page_id": page_id}):
		doc = frappe.get_doc("FB Page Config", {"page_id": page_id})
		doc.page_access_token = final_token
		doc.is_active = 1
		doc.connected_form_ids = form_ids
		doc.save()
	else:
		doc = frappe.new_doc("FB Page Config")
		doc.page_id = page_id
		doc.page_name = page_name
		doc.page_access_token = final_token
		doc.is_active = 1
		doc.connected_form_ids = form_ids
		doc.erpnext_user = frappe.session.user
		doc.insert()

	subscribe_resp = requests.post(
		f"https://graph.facebook.com/v25.0/{page_id}/subscribed_apps",
		params={
			"subscribed_fields": "leadgen",
			"access_token": final_token
		}
	)
	subscribe_data = subscribe_resp.json()
	frappe.log_error(str(subscribe_data), f"Page Subscribe Result: {page_name}")

	frappe.db.commit()
	return {"success": True, "page": page_name}


@frappe.whitelist(allow_guest=True)
def fb_webhook(**kwargs):

	# GET - Meta verification handshake
	if frappe.request.method == "GET":
		args = frappe.request.args
		verify_token = args.get("hub.verify_token")
		challenge = args.get("hub.challenge")
		mode = args.get("hub.mode")

		if mode == "subscribe" and verify_token == frappe.conf.get("fb_verify_token"):
			return Response(challenge, status=200, mimetype="text/plain")

		return Response("Forbidden", status=403, mimetype="text/plain")

	# POST - New lead notification from Meta
	elif frappe.request.method == "POST":
		try:
			data = json.loads(frappe.request.data)
			frappe.log_error(title="FB WEBHOOK PAYLOAD", message=str(data))
			for entry in data.get("entry", []):
				for change in entry.get("changes", []):
					if change.get("field") == "leadgen":
						val = change.get("value", {})
						leadgen_id = val.get("leadgen_id")
						page_id = val.get("page_id")
						form_id = val.get("form_id")
						ad_id = val.get("ad_id", "")

						if leadgen_id and page_id:
							frappe.enqueue(
								"fujishkahr.api.api.process_lead",
								leadgen_id=leadgen_id,
								page_id=page_id,
								form_id=form_id,
								ad_id=ad_id,
								queue="default",
								now=False
							)

		except Exception as e:
			frappe.log_error(title="FB Webhook Error", message=str(e))
		return Response("OK", status=200, mimetype="text/plain")

def process_lead(leadgen_id, page_id, form_id, ad_id=""):
	# Check duplicate
	if frappe.db.exists("Lead", {"custom_fb_lead_id": leadgen_id}):
		frappe.log_error(f"Duplicate lead skipped: {leadgen_id}", "FB Lead Duplicate")
		return

	# Handle TEST leads from Meta Lead Ads Testing Tool
	if "TEST" in str(leadgen_id).upper():
		lead = frappe.new_doc("Lead")
		lead.lead_name = "Facebook Test Lead"
		lead.email_id = f"testlead_{leadgen_id}@facebook.com"
		lead.mobile_no = "0000000000"
		lead.source = "Facebook"
		lead.status = "Lead"
		lead.custom_fb_lead_id = leadgen_id
		lead.custom_fb_page_id = page_id
		lead.custom_fb_form_id = form_id
		lead.custom_sync_status = "Synced"
		lead.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.log_error("Test lead created successfully!", "FB Test Lead")
		return

	# Get page access token
	page_config = frappe.db.get_value(
		"FB Page Config",
		{"page_id": page_id, "is_active": 1},
		"page_access_token"
	)

	if not page_config:
		frappe.log_error(f"No page config found for page_id: {page_id}", "FB Lead Error")
		return

	# Fetch lead data from Graph API
	resp = requests.get(
		f"https://graph.facebook.com/v25.0/{leadgen_id}",
		params={
			"access_token": page_config,
			"fields": "id,created_time,field_data,ad_id,ad_name,form_id,campaign_id,campaign_name"
		}
	)
	lead_data = resp.json()
	frappe.log_error(title="FB LEAD DATA", message=str(lead_data))
	if "error" in lead_data:
		frappe.log_error(title="FB Lead Fetch Error", message=str(lead_data))
		return

	# Parse field_data into dict
	fields = {}
	for item in lead_data.get("field_data", []):
		key = item.get("name", "").lower()
		values = item.get("values", [])
		fields[key] = values[0] if values else ""

	first_name = fields.get("first_name", "")
	last_name = fields.get("last_name", "")
	full_name = fields.get("full_name") or f"{first_name} {last_name}".strip() or "Unknown"
	full_name = re.sub(r'[<>]', '', full_name).strip()
	if not full_name or full_name.startswith("test lead"):
		full_name = "Facebook Test Lead"

	mobile = fields.get("phone_number") or fields.get("phone", "")
	if mobile:
		mobile = re.sub(r'[<>:\s]', '', mobile).strip()
		if not mobile.replace(" ", "").isdigit():
			mobile = ""

	# Create ERPNext Lead
	lead = frappe.new_doc("Lead")
	lead.lead_name = full_name
	lead.email_id = fields.get("email", "")
	lead.mobile_no = mobile
	lead.company_name = fields.get("company_name", "")
	lead.source = "Facebook"
	lead.status = "Lead"
	lead.custom_fb_lead_id = leadgen_id
	lead.custom_fb_page_id = page_id
	lead.custom_fb_form_id = form_id
	lead.custom_fb_ad_name = lead_data.get("ad_name", "")
	lead.custom_fb_campaign_name = lead_data.get("campaign_name", "")
	lead.custom_sync_status = "Synced"
	lead.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.log_error(f"Lead created: {lead.name} for {full_name}", "FB Lead Created")


def save_fb_connection(fb_user_id, access_token, fb_name):
	if frappe.db.exists("FB Connection", {"fb_user_id": fb_user_id}):
		doc = frappe.get_doc("FB Connection", {"fb_user_id": fb_user_id})
		doc.user_access_token = access_token
		doc.fb_name = fb_name
		doc.is_active = 1
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("FB Connection")
		doc.fb_user_id = fb_user_id
		doc.fb_name = fb_name
		doc.user_access_token = access_token
		doc.erpnext_user = frappe.session.user
		doc.is_active = 1
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


@frappe.whitelist()
def get_connection_status():
	connection = frappe.db.get_value(
		"FB Connection",
		{"erpnext_user": frappe.session.user, "is_active": 1},
		["fb_name", "fb_user_id"],
		as_dict=True
	)
	if connection:
		return {"connected": True, "fb_name": connection.fb_name, "fb_user_id": connection.fb_user_id}
	return {"connected": False}


@frappe.whitelist()
def disconnect_fb():
	frappe.db.set_value(
		"FB Connection",
		{"erpnext_user": frappe.session.user},
		"is_active", 0
	)
	frappe.db.commit()
	return {"success": True}