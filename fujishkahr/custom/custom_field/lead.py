def get_lead_custom_fields():
	"""
	Custom fields that need to be added to the Lead DocType
	"""
	return {
		"Lead": [
			{
				"fieldtype": "Section Break",
				"label": "Facebook Lead Info",
				"fieldname": "custom_fb_section",
				"insert_after": "blog_subscriber",
				"collapsible": 1,
			},
			{
				"fieldname": "custom_fb_lead_id",
				"fieldtype": "Data",
				"label": "Facebook Lead ID",
				"insert_after": "custom_fb_section",
			},
			{
				"fieldname": "custom_fb_page_id",
				"fieldtype": "Data",
				"label": "Facebook Page ID",
				"insert_after": "custom_fb_lead_id",
			},
			{
				"fieldname": "custom_fb_form_id",
				"fieldtype": "Data",
				"label": "Facebook Form ID",
				"insert_after": "custom_fb_page_id"
			},
			{
				"fieldname": "custom_fb_ad_name",
				"fieldtype": "Data",
				"label": "Facebook Ad Name",
				"insert_after": "custom_fb_form_id"
			},
			{
				"fieldname": "custom_fb_campaign_name",
				"fieldtype": "Data",
				"label": "Campaign Name",
				"insert_after": "custom_fb_ad_name"
			},
			{
				"fieldname": "custom_sync_status",
				"fieldtype": "Select",
				"label": "Sync Status",
				"insert_after": "custom_fb_campaign_name",
				"options": "Synced\nFailed\nPending"
			},
		]
	}