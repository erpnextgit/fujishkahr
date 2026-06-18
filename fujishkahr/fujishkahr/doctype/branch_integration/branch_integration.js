// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('Branch Integration', {
	refresh: function(frm) {
		filter_branch(frm);

		// Skip if new unsaved record
		if (frm.is_new()) return;

		let has_token   = frm.doc.token ? true : false;
		let status      = frm.doc.branch_erpnext_status;
		let is_accepted = status === "Accepted";
		let is_rejected = status === "Rejected";
		let is_pending  = status === "Pending";

		// Button: Branch Registration
		// Visible when branch is not yet accepted
		if (!is_accepted) {
			frm.add_custom_button(__('Branch Registration'), function() {

				// Validate required fields before calling API
				if (!frm.doc.company_code || !frm.doc.branch_code || !frm.doc.branch_password) {
					frappe.msgprint({
						title: __('Missing Information'),
						indicator: 'orange',
						message: __('Please enter <b>Company Code</b>, <b>Branch Code</b>, and <b>Password</b> before registering.')
					});
					return;
				}

				// If previously rejected, ask for re-register confirmation
				if (is_rejected) {
					frappe.confirm(
						__('This branch was <b>Rejected</b>.<br><br>Do you want to <b>Re-Register</b> with Fujishka API?'),
						function() { call_registration_api(frm); }
					);
					return;
				}

				// If token exists but not rejected, warn before overwriting
				if (has_token) {
					frappe.confirm(
						__('This branch is <b>already registered</b>.<br><br>Re-registering will <b>overwrite</b> the existing Token and Endpoint.<br><br>Are you sure you want to continue?'),
						function() { call_registration_api(frm); }
					);
					return;
				}

				// Fresh registration
				frappe.confirm(
					__('Register this branch with <b>Fujishka API</b>?'),
					function() { call_registration_api(frm); }
				);
			});
		}

		// Button: Check Branch Status
		// Visible only when token exists
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
						if (!res) return;

						if (res.status === "Success") {
							frappe.call({
								method: "frappe.client.set_value",
								args: {
									doctype: "Branch Integration",
									name: frm.doc.name,
									fieldname: {
										branch_erpnext_status:     res.branch_status,
										branch_erpnext_sts_remark: res.remark || ""
									}
								},
								callback: function() {
									frappe.show_alert({
										message: __('Status updated: ') + (res.branch_status || "Unknown"),
										indicator: 'blue'
									});
									frm.reload_doc();
								}
							});
						} else {
							frappe.msgprint({
								title: __('Status Check Failed'),
								indicator: 'red',
								message: `<div style="padding:5px;">
									<p style="color:#d9534f;font-weight:bold;">
										Reason: ${res.error || "Unknown Error"}
									</p>
									<p style="font-size:11px;color:#888;">
										Please check your token and endpoint.
									</p>
								</div>`
							});
						}
					}
				});
			});
		}

		// Button: Request Branch Approval
		// Visible only when token exists, not accepted, not rejected
		if (has_token && !is_accepted && !is_rejected) {
			frm.add_custom_button(__('Request Branch Approval'), function() {
				frappe.confirm(
					__('Are you sure you want to submit an <b>Approval Request</b> to Fujishka?'),
					function() {
						frappe.call({
							method: "call_branch_approval_api",
							args: {
								token:        frm.doc.token,
								endpoint:     frm.doc.endpoint,
								company_code: frm.doc.company_code,
								branch_code:  frm.doc.branch_code
							},
							freeze: true,
							freeze_message: __("Submitting Approval Request..."),
							callback: function(r) {
								let res = r.message;
								if (!res) return;

								if (res.status === "Success") {
									frappe.call({
										method: "frappe.client.set_value",
										args: {
											doctype: "Branch Integration",
											name: frm.doc.name,
											fieldname: {
												branch_erpnext_status:     "Pending",
												branch_erpnext_sts_remark: "Approval request submitted. Waiting for review.",
												approval_response:         res.full_response || ""
											}
										},
										callback: function() {
											frappe.show_alert({
												message: __('Approval Request Submitted Successfully'),
												indicator: 'green'
											});
											frm.reload_doc();
										}
									});
								} else {
									frappe.call({
										method: "frappe.client.set_value",
										args: {
											doctype: "Branch Integration",
											name: frm.doc.name,
											fieldname: {
												approval_response: res.full_response || ""
											}
										}
									});
									frappe.msgprint({
										title: __('Approval Request Failed'),
										indicator: 'red',
										message: `<div style="padding:5px;">
											<p style="color:#d9534f;font-weight:bold;">
												Reason: ${res.error || "Unknown Error"}
											</p>
											<p style="font-size:11px;color:#888;">
												Please try again or contact Fujishka support.
											</p>
										</div>`
									});
								}
							}
						});
					}
				);
			});
		}

		// Banners — show current branch status at top
		// clear first to prevent duplicate banners
		frm.dashboard.clear_headline();

		if (is_accepted) {
			frm.dashboard.set_headline_alert(
				'<div style="color:green;font-weight:bold;">✅ Branch is Accepted and Active!</div>'
			);
		} else if (is_rejected) {
			let remark = frm.doc.branch_erpnext_sts_remark
				? `<br><span style="font-size:12px;font-weight:normal;">Reason: ${frm.doc.branch_erpnext_sts_remark}</span>`
				: '';
			frm.dashboard.set_headline_alert(
				`<div style="color:red;font-weight:bold;">❌ Branch Rejected. Please Re-Register.${remark}</div>`
			);
		} else if (is_pending) {
			frm.dashboard.set_headline_alert(
				'<div style="color:orange;font-weight:bold;">⏳ Branch Approval is Pending. Please wait for Fujishka review.</div>'
			);
		} else if (!has_token) {
			frm.dashboard.set_headline_alert(
				'<div style="color:#555;font-weight:bold;">ℹ️ Branch not registered yet. Click "Branch Registration" to begin.</div>'
			);
		}

		// Field Locking
		// Lock credentials if token exists and not rejected
		// Unlock if rejected so user can fix and re-register
		let should_lock = has_token && !is_rejected;
		frm.set_df_property('company_code',    'read_only', should_lock ? 1 : 0);
		frm.set_df_property('branch_code',     'read_only', should_lock ? 1 : 0);
		frm.set_df_property('branch_password', 'read_only', should_lock ? 1 : 0);
	},
	onload: function(frm) {
		// Filter branch options based on selected company
		filter_branch(frm);
	},
	company_code: function(frm) {
		// Clear branch field when company code changes
		frm.set_value('branch', null);
		filter_branch(frm);
	},
	company: function(frm) {
		// Clear branch field when company changes
		frm.set_value('branch', null);
		filter_branch(frm);
	},
});

// Registration API Call
// Used for both fresh registration and re-registration
function call_registration_api(frm) {
	// Step 1: Generate callback token first
	frappe.call({
		method: "fujishkahr.api.api.generate_callback_token",
		args: { branch_name: frm.doc.name },
		freeze: true,
		freeze_message: __("Preparing Registration..."),
		callback: function(token_res) {
			let callback_token = token_res.message;

			if (!callback_token) {
				frappe.msgprint({
					title: __('Error'),
					indicator: 'red',
					message: __('Failed to generate callback token.')
				});
				return;
			}

			// Step 2: Call registration API with callback_token
			frappe.call({
				method: "call_external_registration_api",
				args: {
					company_code:    frm.doc.company_code,
					branch_code:     frm.doc.branch_code,
					branch_password: frm.doc.branch_password,
					base_url:        window.location.origin,
					branch_name:     frm.doc.name,
					callback_token:  callback_token
				},
				freeze: true,
				freeze_message: __("Connecting to Fujishka API..."),
				callback: function(r) {
					let res = r.message;
					if (!res) return;

					if (res.status === "Success") {
						// Step 3: Save all fields to Branch Integration
						frappe.call({
							method: "frappe.client.set_value",
							args: {
								doctype: "Branch Integration",
								name: frm.doc.name,
								fieldname: {
									token:                     res.token,
									endpoint:                  res.endpoint,
									callback_token:            callback_token,
									branch_erpnext_status:     "",
									branch_erpnext_sts_remark: "Registered successfully. Please request approval.",
									api_response:              res.full_response || ""
								}
							},
							callback: function() {
								frappe.show_alert({
									message: __('Registration Successful! Now click "Request Branch Approval".'),
									indicator: 'green'
								});
								frm.reload_doc();
							}
						});

					} else {
						frappe.msgprint({
							title: __('Registration Failed'),
							indicator: 'red',
							message: `<div style="padding:5px;">
								<p style="color:#d9534f;font-weight:bold;">
									Reason: ${res.error || "Unknown Error"}
								</p>
								<p style="font-size:11px;color:#888;">
									Please check your Company Code, Branch Code and Password.
								</p>
							</div>`
						});
					}
				}
			});
		}
	});
}

/*
 * function to filter branch field based on selected company
 * only branches of the same company will be shown in the branch field
 */
function filter_branch(frm) {
	frm.set_query("branch", function() {
		return {
			filters: {
				"company": frm.doc.company
			}
		}
	})
}