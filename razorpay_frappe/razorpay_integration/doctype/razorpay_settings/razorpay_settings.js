// Copyright (c) 2024, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Razorpay Settings", {
	refresh(frm) {
		frm.sidebar
			.add_user_action(__("Copy Webhook Endpoint"))
			.attr("href", "#")
			.on("click", () => {
				const baseUrl = frappe.urllib.get_base_url();
				const webhookEndpoint = `${baseUrl}/razorpay/webhook-handler`;
				frappe.utils.copy_to_clipboard(webhookEndpoint, __("Webhook endpoint copied"));
			});
	},
});
