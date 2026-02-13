// // Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Branch Registration', {
//     refresh: function(frm) {
//         // Only show button if the document is saved
//         frm.add_custom_button(__('Branch Registration'), function() {
            
//             // Check if required fields are filled
//             if(!frm.doc.company_code || !frm.doc.branch_code || !frm.doc.branch_password) {
//                 frappe.msgprint(__('Please enter Company Code, Branch Code, and Password first.'));
//                 return;
//             }

//             frappe.call({
//                 method: "call_external_registration_api", 
//                 args: {
//                     // Since it is now a Data field, we use frm.doc directly
//                     company_code: frm.doc.company_code,
//                     branch_code: frm.doc.branch_code,
//                     branch_password: frm.doc.branch_password 
//                 },
//                 freeze: true,
//                 freeze_message: __("Connecting to Fujishka API..."),
//                 callback: function(r) {
//                     if (r.message) {
//                         let res = r.message;
                        
//                         // Update status and response log
//                         frm.set_value('status', res.status);
//                         frm.set_value('api_response', res.full_response);

//                         if (res.status === "Success") {
//                             frm.set_value('token', res.token);
//                             frm.set_value('endpoint', res.endpoint);
//                             frappe.show_alert({message: __('Registration Successful'), indicator: 'green'});
//                         } else {
//                             frappe.msgprint({
//                                 title: __('API Failed'),
//                                 indicator: 'red',
//                                 message: res.error
//                             });
//                         }
                        
//                         // Save the form to store the token and status
//                         frm.save();
//                     }
//                 }
//             });
//         });
//     }
// });

frappe.ui.form.on('Branch Registration', {
    refresh: function(frm) {
        frm.add_custom_button(__('Branch Registration'), function() {
            
            if(!frm.doc.company_code || !frm.doc.branch_code || !frm.doc.branch_password) {
                frappe.msgprint(__('Please enter Company Code, Branch Code, and Password first.'));
                return;
            }

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
                        // Update fields
                        frm.set_value('status', res.status);
                        frm.set_value('api_response', res.full_response);

                        if (res.status === "Success") {
                            frm.set_value('token', res.token);
                            frm.set_value('endpoint', res.endpoint);
                            frappe.show_alert({message: __('Registration Successful'), indicator: 'green'});
                        } else {
                            // --- SAFETY GRABBER START ---
                            let raw = res.full_response || "";
                            let error_to_show = res.error;

                            // If error is blank, manually pull it from the raw string
                            if (!error_to_show && raw.includes('error":"')) {
                                error_to_show = raw.split('error":"')[1].split('"')[0];
                            }
                            
                            // Final fallback so it is NEVER blank
                            if (!error_to_show) { error_to_show = "Action Failed (Check API Response field)"; }
                            // --- SAFETY GRABBER END ---

                            frappe.msgprint({
                                title: __('API Registration Failed: Check Code and Password'),
                                indicator: 'red',
                                message: `
                                    <div style="padding: 5px;">
                                        <p style="color: #d9534f; font-weight: bold;">Reason: ${error_to_show}</p>
                                    </div>
                                `
                            });
                        }
                        frm.save();
                    }
                }
            });
        });
    }
});