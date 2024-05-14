# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.utils import (
	RazorpayWebhookEvents,
)

SUPPORTED_WEBHOOK_EVENTS = set(RazorpayWebhookEvents)


class RazorpayWebhookLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		event: DF.Data | None
		order_id: DF.Data | None
		payload: DF.Code | None
		payment_id: DF.Data | None
	# end: auto-generated types

	def on_submit(self):
		order_exists = frappe.db.exists(
			"Razorpay Order", {"order_id": self.order_id}
		)

		if not order_exists:
			return

		if self.event not in SUPPORTED_WEBHOOK_EVENTS:
			return

		order_doc: RazorpayOrder = frappe.get_doc(
			"Razorpay Order", {"order_id": self.order_id}
		)
		payload = frappe.parse_json(self.payload)
		order_doc.handle_webhook_event(self.event, payload)
