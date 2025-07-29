// Copyright (c) 2024, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Razorpay Order", {
	refresh(frm) {
		if (frm.doc.status === "Paid") {
			frm.add_custom_button("Refund", () => {
				frappe.confirm("Are you sure you want to refund in full?", () => {
					frm.call("refund").then(({ message }) => {
						if (message != "failed") {
							frappe.show_alert("Refund Processed");
							frm.refresh();
						}
					});
				});
			});
		}

		const btn = frm.add_custom_button("Sync Status", () => {
			frm.call({ method: "sync_status", btn, doc: frm.doc }).then(() => {
				frappe.show_alert("Latest status synced");
				frm.refresh();
			});
		});

		frm.add_web_link(
			`https://dashboard.razorpay.com/app/orders/${frm.doc.order_id}?init_point=orders-table&init_page=Transactions.Orders`,
			"View in Razorpay Dashboard"
		)
	},
});
