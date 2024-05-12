# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.utils import (
	convert_from_razorpay_money,
	get_in_razorpay_money,
	get_razorpay_client,
)


class RazorpayOrder(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		contact: DF.Data | None
		currency: DF.Link | None
		customer_email: DF.Data | None
		fee: DF.Currency
		meta_data: DF.Code | None
		method: DF.Data | None
		name: DF.Int | None
		order_id: DF.Data
		payment_id: DF.Data | None
		ref_dn: DF.DynamicLink | None
		ref_dt: DF.Link | None
		status: DF.Literal[
			"Pending", "Failed", "Paid", "Refund in Progress", "Refunded"
		]
		tax: DF.Currency
	# end: auto-generated types

	@staticmethod
	def initiate(
		amount: int,
		currency: str = "INR",
		meta_data: dict | None = None,
		ref_dt: str | None = None,
		ref_dn: str | None = None,
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
			ref_dt=ref_dt,
			ref_dn=ref_dn,
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

		order: RazorpayOrder = frappe.get_doc(
			"Razorpay Order", {"order_id": order_id}
		)
		order.status = "Paid"
		order.payment_id = payment_id
		order.set_payment_details()
		order.save(ignore_permissions=True)

	def set_payment_details(self):
		if frappe.flags.in_test:
			return

		if not self.payment_id:
			return

		client = get_razorpay_client()
		payment = client.payment.fetch(self.payment_id)
		self.fee = convert_from_razorpay_money(payment.get("fee", 0))
		self.tax = convert_from_razorpay_money(payment.get("tax", 0))
		self.method = payment.get("method")
		self.contact = payment.get("contact")

	@frappe.whitelist()
	def refund(self):
		frappe.only_for("System Manager")

		if not self.is_paid:
			frappe.throw("Refunds Can be Made Only on Paid Payments!")

		client = get_razorpay_client()
		refund_amount = int(get_in_razorpay_money(self.amount))
		refund = client.payment.refund(self.payment_id, refund_amount)

		self.refund_id = refund["id"]
		if refund["status"] == "processed":
			self.status = "Refunded"
		elif refund["status"] == "pending":
			self.status = "Refund Pending"

		self.save()

		return refund["status"]

	@frappe.whitelist()
	def sync_status(self):
		client = get_razorpay_client()
		order = client.order.fetch(self.order_id)
		payments = client.order.payments(self.order_id).get("items", [])

		if order["status"] == "paid":
			frappe.errprint(payments)
			if payments[0]["status"] == "captured" and self.status != "Paid":
				self.status = "Paid"
				self.payment_id = payments[0]["id"]
			elif payments[0]["status"] == "refunded":
				self.status = "Refunded"
		elif order["status"] == "created" and self.status != "Pending":
			self.status = "Pending"

		self.set_payment_details()
		self.save()

	@property
	def is_paid(self):
		return self.status == "Paid"
