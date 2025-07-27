# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import get_timestamp

from razorpay_frappe.utils import get_in_razorpay_money, get_razorpay_client


class RazorpayPaymentLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		callback_url: DF.Data | None
		currency: DF.Link
		customer_contact: DF.Phone | None
		customer_email: DF.Data | None
		customer_name: DF.Data | None
		description: DF.SmallText | None
		expire_by: DF.Date | None
		id: DF.Data | None
		short_url: DF.Data | None
		status: DF.Literal["Created", "Partially Paid", "Expired", "Cancelled", "Paid"]
		type: DF.Literal["Standard", "UPI"]
	# end: auto-generated types

	def before_insert(self):
		payment_link = self.create_payment_link_on_razorpay()

		self.id = payment_link["id"]
		self.short_url = payment_link["short_url"]
		self.status = frappe.unscrub(payment_link["status"])

	def create_payment_link_on_razorpay(self):
		client = get_razorpay_client()
		return client.payment_link.create(
			{
				"amount": get_in_razorpay_money(self.amount),
				"description": self.description,
				"currency": self.currency,
				"customer": {
					"name": self.customer_name,
					"email": self.customer_email,
					"contact": self.customer_contact,
				},
				"upi_link": self.type == "UPI",
				"expire_by": get_timestamp(self.expire_by),
			}
		)

	@frappe.whitelist()
	def fetch_latest_status(self):
		client = get_razorpay_client()
		payment_link = client.payment_link.fetch(self.id)
		link_status = frappe.unscrub(payment_link["status"])
		if link_status != self.status:
			self.status = link_status
			self.save()
