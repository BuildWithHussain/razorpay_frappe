# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.utils import (
	convert_from_razorpay_money,
)


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
		payload = frappe.parse_json(self.payload)
		payment_entity = payload["payload"]["payment"]["entity"]
		customer_email = payment_entity.get("email")

		order_exists = frappe.db.exists(
			"Razorpay Order", {"order_id": self.order_id}
		)

		if not order_exists:
			return

		order_doc = frappe.get_doc(
			"Razorpay Order", {"order_id": self.order_id}
		)

		if self.event == "payment.captured" and order_doc.status != "Paid":
			order_doc.status = "Paid"
			order_doc.fee = convert_from_razorpay_money(
				payment_entity.get("fee", 0)
			)
			order_doc.tax = convert_from_razorpay_money(
				payment_entity.get("tax", 0)
			)
			order_doc.method = payment_entity.get("method")
			order_doc.contact = payment_entity.get("contact")
		elif (
			self.event == "refund.processed"
			and not order_doc.status == "Refunded"
		):
			refund_entity = payload["payload"]["refund"]["entity"]
			order_doc.status = "Refunded"
			order_doc.refund_id = refund_entity["id"]

		order_doc.customer_email = customer_email
		order_doc.save()
