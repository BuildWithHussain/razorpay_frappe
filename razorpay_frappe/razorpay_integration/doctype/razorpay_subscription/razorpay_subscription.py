# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document

from razorpay_frappe.razorpay_integration.doctype.razorpay_note_item.razorpay_note_item import (
	RazorpayNoteItem,
)
from razorpay_frappe.utils import (
	convert_from_razorpay_money,
	get_razorpay_client,
)
from razorpay_frappe.webhook_processor import (
	RazorpaySubscriptionWebhookEvents,
)


class RazorpaySubscription(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from razorpay_frappe.razorpay_integration.doctype.razorpay_note_item.razorpay_note_item import (
			RazorpayNoteItem,
		)

		customer_id: DF.Data | None
		ended_at: DF.Date | None
		id: DF.Data | None
		notes: DF.Table[RazorpayNoteItem]
		notify_customer_via_razorpay: DF.Check
		plan_id: DF.Link
		short_url: DF.Data | None
		status: DF.Literal[
			"Created",
			"Authenticated",
			"Active",
			"Pending",
			"Halted",
			"Cancelled",
			"Completed",
			"Expired",
			"Paused",
		]
		total_count: DF.Int
	# end: auto-generated types

	def before_insert(self):
		subscription = self.create_subscription_on_razorpay()

		self.id = subscription.get("id")
		self.status = frappe.unscrub(subscription.get("status"))
		self.short_url = subscription.get("short_url")

	def create_subscription_on_razorpay(self):
		client = get_razorpay_client()

		return client.subscription.create(
			{
				"plan_id": self.plan_id,
				"customer_notify": 1
				if self.notify_customer_via_razorpay
				else 0,
				"total_count": self.total_count or 12,
				"notes": RazorpayNoteItem.get_as_dict(self.notes),
			}
		)

	@frappe.whitelist()
	def fetch_latest_status(self):
		client = get_razorpay_client()
		subscription = client.subscription.fetch(self.id)
		subscription_status = frappe.unscrub(subscription.get("status"))

		if self.status != subscription_status:
			self.status = subscription_status
			self.save()

	def handle_webhook_event(self, event: str, payload: dict):
		from datetime import datetime

		if event == RazorpaySubscriptionWebhookEvents.SubscriptionCancelled:
			end_timestamp = payload["subscription"]["entity"]["ended_at"]
			self.ended_at = datetime.utcfromtimestamp(end_timestamp)
			self.status = "Cancelled"
			self.save()
		elif (
			event == RazorpaySubscriptionWebhookEvents.SubscriptionAuthenticated
		):
			self.status = "Authenticated"
			self.customer_id = payload["subscription"]["entity"]["customer_id"]
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionCompleted:
			self.status = "Completed"
			end_timestamp = payload["subscription"]["entity"]["ended_at"]
			self.ended_at = datetime.utcfromtimestamp(end_timestamp)
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionActivated:
			self.status = "Active"

			# handle upfront charge (if applicable)
			if payload["subscription"]["entity"].get("type") == 2:
				self.record_charge_for_subscription(payload)

			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionCharged:
			subscription_entity = payload["subscription"]["entity"]
			self.status = frappe.unscrub(subscription_entity.get("status"))
			self.record_charge_for_subscription(payload)
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionHalted:
			self.status = "Halted"
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionPaused:
			self.status = "Paused"
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionResumed:
			self.status = "Active"
			self.save()
		elif event == RazorpaySubscriptionWebhookEvents.SubscriptionPending:
			self.status = "Pending"
			self.save()

	def record_charge_for_subscription(self, webhook_payload: dict):
		payment_entity = webhook_payload["payment"]["entity"]
		frappe.get_doc(
			{
				"doctype": "Razorpay Order",
				"type": "Subscription",
				"order_id": payment_entity["order_id"],
				"subscription": self.name,
				"payment_id": payment_entity["id"],
				"invoice_id": payment_entity["invoice_id"],
				"fee": convert_from_razorpay_money(payment_entity["fee"]),
				"tax": convert_from_razorpay_money(payment_entity["tax"]),
				"customer_email": payment_entity["email"],
				"method": payment_entity["method"],
				"contact": payment_entity["contact"],
				"customer_id": payment_entity.get("customer_id"),
				"status": "Paid",
			}
		).save()
