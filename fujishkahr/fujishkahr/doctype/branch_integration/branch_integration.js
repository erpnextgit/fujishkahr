frappe.ui.form.on('Branch Integration', {
    refresh: function(frm) {
        // Only show button if the document is saved
        frm.add_custom_button(__('Register Branch'), function() {
            
            // Check if required fields are filled
            if(!frm.doc.company_code || !frm.doc.branch_code || !frm.doc.branch_password) {
                frappe.msgprint(__('Please enter Company Code, Branch Code, and Password first.'));
                return;
            }

            frappe.call({
                method: "call_external_registration_api", 
                args: {
                    // Since it is now a Data field, we use frm.doc directly
                    company_code: frm.doc.company_code,
                    branch_code: frm.doc.branch_code,
                    branch_password: frm.doc.branch_password 
                },
                freeze: true,
                freeze_message: __("Connecting to Fujishka API..."),
                callback: function(r) {
                    if (r.message) {
                        let res = r.message;
                        
                        // Update status and response log
                        frm.set_value('status', res.status);
                        frm.set_value('api_response', res.full_response);

                        if (res.status === "Success") {
                            frm.set_value('token', res.token);
                            frm.set_value('endpoint', res.endpoint);
                            frappe.show_alert({message: __('Registration Successful'), indicator: 'green'});
                        } else {
                            frappe.msgprint({
                                title: __('API Failed'),
                                indicator: 'red',
                                message: res.error
                            });
                        }
                        
                        // Save the form to store the token and status
                        frm.save();
                    }
                }
            });
        });
    }
});
