// Copyright (c) 2024, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Razorpay Payment Link", {
	refresh(frm) {
		const paymentLink = frm.doc.short_url;
		if (paymentLink && !["Paid", "Expired"].includes(frm.doc.status)) {
			frm.add_custom_button("Copy Payment Link", () => {
				frappe.utils.copy_to_clipboard(paymentLink, "Payment Link copied");
			});
		}

		if (frm.doc.status !== "Expired") {
			frm.add_custom_button("Fetch Status", () => {
				frm.call("fetch_latest_status").then(() => {
					frappe.show_alert("Latest status updated");
					frm.refresh();
				});
			});
		}
	},
});
