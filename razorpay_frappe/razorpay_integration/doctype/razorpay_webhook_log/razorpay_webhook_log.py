# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from razorpay_frappe.webhook_processor import WebhookProcessor


class RazorpayWebhookLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		event: DF.Data | None
		payload: DF.Code | None
	# end: auto-generated types

	def on_submit(self):
		payload = frappe.parse_json(self.payload)
		processor = WebhookProcessor(self.event, payload)
		processor.process()
