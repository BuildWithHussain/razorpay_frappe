# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.utils import get_in_razorpay_money, get_razorpay_client


class RazorpayOrder(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		currency: DF.Link | None
		customer_email: DF.Data | None
		meta_data: DF.Code | None
		name: DF.Int | None
		order_id: DF.Data
		payment_id: DF.Data | None
		status: DF.Literal[
			"Pending", "Failed", "Paid", "Refund in Progress", "Refunded"
		]
	# end: auto-generated types

	@staticmethod
	def initiate(
		amount: int, currency: str = "INR", meta_data: dict | None = None
	) -> dict:
		if meta_data is None:
			meta_data = {}
		meta_data = frappe.as_json(meta_data, indent=2)

		client = get_razorpay_client()
		_order = client.order.create(
			data={
				"amount": get_in_razorpay_money(amount),
				"currency": currency,
			}
		)

		order_doc = frappe.get_doc(
			doctype="Razorpay Order",
			order_id=_order["id"],
			amount=amount,
			currency=currency,
			meta_data=meta_data,
			status="Pending",
		)
		order_doc.insert(ignore_permissions=True)

		return {"key_id": client.auth[0], "order_id": _order["id"]}

	@staticmethod
	def handle_failure(order_id: str):
		if frappe.db.exists("Razorpay Order", {"order_id": order_id}):
			doc: RazorpayOrder = frappe.get_doc(
				"Razorpay Order", {"order_id": order_id}
			)
			doc.mark_as_failed()
		else:
			frappe.throw(f"Razorpay Order: {order_id} not found!")

	def mark_as_failed(self):
		self.status = "Failed"
		self.save(ignore_permissions=True)

	@staticmethod
	def handle_success(order_id: str, payment_id: str, signature: str):
		client = get_razorpay_client()

		if not frappe.flags.in_test:
			client.utility.verify_payment_signature(
				{
					"razorpay_order_id": order_id,
					"razorpay_payment_id": payment_id,
					"razorpay_signature": signature,
				}
			)

		order = frappe.get_doc("Razorpay Order", {"order_id": order_id})
		order.status = "Paid"
		order.payment_id = payment_id

		order.save(ignore_permissions=True)
