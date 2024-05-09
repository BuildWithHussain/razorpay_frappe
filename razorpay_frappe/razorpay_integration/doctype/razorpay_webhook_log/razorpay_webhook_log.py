# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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

	pass
