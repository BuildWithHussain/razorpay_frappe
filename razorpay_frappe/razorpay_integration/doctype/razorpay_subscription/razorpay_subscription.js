// Copyright (c) 2024, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Razorpay Subscription", {
	refresh(frm) {
		const subscriptionPageLink = frm.doc.short_url;
		if (subscriptionPageLink) {
			frm.add_web_link(subscriptionPageLink, "View Subscription Page");
		}

		if (frm.doc.status !== "Expired" && !frm.is_new()) {
			frm.add_custom_button("Fetch Status", () => {
				frm.call("fetch_latest_status").then(() => {
					frappe.show_alert("Latest status updated");
					frm.refresh();
				});
			});
		}
	},
});
