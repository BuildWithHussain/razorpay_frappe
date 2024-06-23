# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.razorpay_integration.doctype.razorpay_note_item.razorpay_note_item import (
	RazorpayNoteItem,
)
from razorpay_frappe.utils import get_in_razorpay_money, get_razorpay_client


class RazorpayPlan(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from razorpay_frappe.razorpay_integration.doctype.razorpay_note_item.razorpay_note_item import (
			RazorpayNoteItem,
		)

		currency: DF.Link
		id: DF.Data | None
		interval: DF.Int
		item_amount: DF.Currency
		item_description: DF.Data | None
		item_id: DF.Data | None
		item_name: DF.Data
		notes: DF.Table[RazorpayNoteItem]
		period: DF.Literal["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
	# end: auto-generated types

	def before_insert(self):
		razorpay_plan = self.create_plan_on_razorpay()

		self.id = razorpay_plan.get("id")
		self.item_id = razorpay_plan.get("item", {}).get("id")

	def create_plan_on_razorpay(self):
		client = get_razorpay_client()

		return client.plan.create(
			{
				"period": frappe.scrub(self.period),
				"interval": self.interval,
				"item": {
					"name": self.item_name,
					"amount": get_in_razorpay_money(self.item_amount),
					"currency": self.currency,
					"description": self.item_description,
				},
				"notes": RazorpayNoteItem.get_as_dict(self.notes),
			}
		)
