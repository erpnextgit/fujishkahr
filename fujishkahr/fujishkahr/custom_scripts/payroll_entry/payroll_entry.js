frappe.ui.form.on('Payroll Entry', {
	refresh: function(frm) {
		show_cancel_status_message(frm);

		if (frm.doc.docstatus === 1 && frm.doc.custom_api_pushed === 1) {
			frm.page.btn_secondary.hide();
		}

		// Hide Make Bank Entry button
		setTimeout(function() {
			$('[data-label="Make%20Bank%20Entry"]').hide();
		}, 300);

		// Show Request Cancellation button always when submitted + api pushed
		if (
			frm.doc.docstatus === 1 &&
			frm.doc.custom_api_pushed === 1
		) {
			frm.add_custom_button(__('Request Cancellation'), function() {
				frappe.prompt(
					[{
						label: 'Reason for Cancellation',
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					}],
					function(values) {
						frappe.confirm(
							__('Are you sure you want to request cancellation?'),
							function() {
								frappe.call({
									method: 'fujishkahr.api.payroll.request_cancellation',
									args: {
										payroll_id: frm.doc.name,
										reason: values.reason
									},
									freeze: true,
									freeze_message: __('Sending Cancel Request...'),
									callback: function(r) {
										if (r.message && r.message.status === 'success') {
											frappe.show_alert({
												message: __('Cancellation request sent successfully!'),
												indicator: 'green'
											}, 5);
											frm.reload_doc();
										} else {
											frappe.show_alert({
												message: __('Failed: ') + (r.message.error || 'Unknown error'),
												indicator: 'red'
											}, 5);
										}
									}
								});
							}
						);
					},
					__('Request Cancellation'),
					__('Submit Request')
				);
			}, __('Actions'));
		}
	},
	custom_cancel_status(frm) {
		show_cancel_status_message(frm);
	},
});

function show_cancel_status_message(frm) {
	frm.dashboard.clear_headline();

	const status = frm.doc.custom_cancel_status;
	const reason = frm.doc.custom_cancel_reason || "";
	const rejection_reason = frm.doc.custom_cancel_rejection_reason || "";

if (rejection_reason) {
	frm.dashboard.set_headline(
		`<span style="color: #060659;">
			<b>Cancellation Rejected</b> — ${rejection_reason}.
			You can cancel this payroll by deleting the referenced journal entry.
		</span>`
	);
}
}