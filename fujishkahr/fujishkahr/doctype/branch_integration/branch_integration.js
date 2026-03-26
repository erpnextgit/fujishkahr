// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('Branch Integration', {
	refresh: function(frm) {

		// ─── No buttons if new record ───
		if (frm.is_new()) return;

		let has_token = frm.doc.token ? true : false;
		let status = frm.doc.branch_erpnext_status;
		let is_accepted = status === "Accepted";
		let is_rejected = status === "Rejected";
		let is_pending = status === "Pending";

		// ─── BUTTON 1: Branch Registration ───
		// Show if no token, rejected, or pending (re-register with warning)
		if (!is_accepted) {
			frm.add_custom_button(__('Branch Registration'), function() {
				if (!frm.doc.company_code || !frm.doc.branch_code || !frm.doc.branch_password) {
					frappe.msgprint(__('Please enter Company Code, Branch Code, and Password first.'));
					return;
				}

				// Already registered with token — show strong warning
				if (has_token && !is_rejected) {
					frappe.confirm(
						__('⚠️ This branch is already registered!\n\nRe-registering will overwrite the existing Token and Endpoint.\n\nAre you sure you want to continue?'),
						function() {
							call_registration_api(frm);
						}
					);
					return;
				}

				// Rejected — show re-register message
				if (is_rejected) {
					frappe.confirm(
						__('❌ This branch was Rejected.\n\nDo you want to Re-Register with Fujishka API?'),
						function() {
							call_registration_api(frm);
						}
					);
					return;
				}

				// Fresh registration — no token yet
				frappe.confirm(
					__('Register this branch with Fujishka API?'),
					function() {
						call_registration_api(frm);
					}
				);
			});
		}

		// ─── BUTTON 2: Check Branch Status ───
		// Show ONLY if token exists
		if (has_token) {
			frm.add_custom_button(__('Check Branch Status'), function() {
				frappe.call({
					method: "call_branch_status_api",
					args: {
						token: frm.doc.token,
						endpoint: frm.doc.endpoint
					},
					freeze: true,
					freeze_message: __("Checking Branch Status..."),
					callback: function(r) {
						let res = r.message;
						if (res) {
							if (res.status === "Success") {
								frm.set_value('branch_erpnext_status', res.branch_status);
								frm.set_value('branch_erpnext_sts_remark', res.remark || "");
								frm.save();
								frappe.show_alert({
									message: __('Status: ') + (res.branch_status || "Not Applied Yet"),
									indicator: 'blue'
								});
							} else {
								frappe.msgprint({
									title: __('Status Check Failed'),
									indicator: 'red',
									message: `<div style="padding:5px;">
										<p style="color:#d9534f;font-weight:bold;">
										Reason: ${res.error}</p></div>`
								});
							}
						}
					}
				});
			});
		}

		// ─── BUTTON 3: Request Approval ───
		// Show ONLY if token exists AND not accepted AND not rejected
		if (has_token && !is_accepted && !is_rejected) {
			frm.add_custom_button(__('Request Branch Approval'), function() {
				frappe.confirm(
					__('Are you sure you want to submit an Approval Request?'),
					function() {
						frappe.call({
							method: "call_branch_approval_api",
							args: {
								token: frm.doc.token,
								endpoint: frm.doc.endpoint,
								company_code: frm.doc.company_code,
								branch_code: frm.doc.branch_code
							},
							freeze: true,
							freeze_message: __("Submitting Approval Request..."),
							callback: function(r) {
								let res = r.message;
								if (res) {
									frm.set_value('approval_response', res.full_response);
									if (res.status === "Success") {
										frappe.show_alert({
											message: __('Approval Request Submitted Successfully'),
											indicator: 'green'
										});
									} else {
										frappe.msgprint({
											title: __('Approval Request Failed'),
											indicator: 'red',
											message: `<div style="padding:5px;">
												<p style="color:#d9534f;font-weight:bold;">
												Reason: ${res.error}</p></div>`
										});
									}
									frm.save();
								}
							}
						});
					}
				);
			});
		}

		// ─── Green Banner if Accepted ───
		if (is_accepted) {
			frm.dashboard.set_headline_alert(
				'<div style="color:green;font-weight:bold;">✅ Branch is Accepted and Active!</div>'
			);
		}

		// ─── Red Banner if Rejected ───
		if (is_rejected) {
			frm.dashboard.set_headline_alert(
				'<div style="color:red;font-weight:bold;">❌ Branch Rejected. Please Re-Register.</div>'
			);
		}

		// ─── Orange Banner if Pending ───
		if (is_pending) {
			frm.dashboard.set_headline_alert(
				'<div style="color:orange;font-weight:bold;">⏳ Branch Approval is Pending.</div>'
			);
		}

		// ─── Lock fields if token exists and not rejected ───
		if (has_token && !is_rejected) {
			frm.set_df_property('company_code', 'read_only', 1);
			frm.set_df_property('branch_code', 'read_only', 1);
			frm.set_df_property('branch_password', 'read_only', 1);
		}
	}
});

function call_registration_api(frm) {
	frappe.call({
		method: "call_external_registration_api",
		args: {
			company_code: frm.doc.company_code,
			branch_code: frm.doc.branch_code,
			branch_password: frm.doc.branch_password
		},
		freeze: true,
		freeze_message: __("Connecting to Fujishka API..."),
		callback: function(r) {
			let res = r.message;
			if (res) {
				frm.set_value('status', res.status);
				frm.set_value('api_response', res.full_response);
				if (res.status === "Success") {
					frm.set_value('token', res.token);
					frm.set_value('endpoint', res.endpoint);
					frappe.show_alert({
						message: __('Registration Successful'),
						indicator: 'green'
					});
				} else {
					let raw = res.full_response || "";
					let error_to_show = res.error;
					if (!error_to_show && raw.includes('error":"')) {
						error_to_show = raw.split('error":"')[1].split('"')[0];
					}
					if (!error_to_show) {
						error_to_show = "Action Failed";
					}
					frappe.msgprint({
						title: __('Registration Failed'),
						indicator: 'red',
						message: `<div style="padding:5px;">
							<p style="color:#d9534f;font-weight:bold;">
							Reason: ${error_to_show}</p></div>`
					});
				}
				frm.save();
			}
		}
	});
}