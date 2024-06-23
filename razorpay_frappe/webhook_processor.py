from enum import StrEnum
from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
		RazorpayOrder,
	)
	from razorpay_frappe.razorpay_integration.doctype.razorpay_subscription.razorpay_subscription import (
		RazorpaySubscription,
	)


class RazorpayPaymentWebhookEvents(StrEnum):
	PaymentCaptured = "payment.captured"
	RefundProcessed = "refund.processed"


class RazorpaySubscriptionWebhookEvents(StrEnum):
	SubscriptionAuthenticated = "subscription.authenticated"
	SubscriptionActivated = "subscription.activated"
	SubscriptionCharged = "subscription.charged"
	SubscriptionCompleted = "subscription.completed"
	SubscriptionUpdated = "subscription.updated"
	SubscriptionPending = "subscription.pending"
	SubscriptionHalted = "subscription.halted"
	SubscriptionCancelled = "subscription.cancelled"
	SubscriptionPaused = "subscription.paused"
	SubscriptionResumed = "subscription.resumed"


SUPPORTED_WEBHOOK_EVENTS = set(RazorpayPaymentWebhookEvents).union(
	RazorpaySubscriptionWebhookEvents
)


class WebhookProcessor:
	def __init__(self, event: str, payload: dict):
		self.event = event
		self.payload = payload

		# set to inner payload object
		if "payload" in self.payload:
			self.payload = self.payload["payload"]

	def process(self):
		if not self.should_process():
			return

		if self.is_subscription_event:
			self.process_subscription_event()
		elif self.is_standalone_order:
			self.process_standalone_order()

	def should_process(self) -> bool:
		return self.is_supported_event

	@property
	def is_supported_event(self) -> bool:
		return self.event in SUPPORTED_WEBHOOK_EVENTS

	def process_subscription_event(self):
		subscription_id = self.get_subscription_id()
		subscription_doc: "RazorpaySubscription" = frappe.get_doc(
			"Razorpay Subscription", subscription_id
		)
		subscription_doc.handle_webhook_event(self.event, self.payload)

	@property
	def is_subscription_event(self) -> bool:
		return self.event in set(RazorpaySubscriptionWebhookEvents)

	def process_standalone_order(self):
		order_doc: "RazorpayOrder" = frappe.get_doc(
			"Razorpay Order", {"order_id": self.get_payment_order_id()}
		)
		order_doc.handle_webhook_event(self.event, self.payload)

	@property
	def is_standalone_order(self) -> bool:
		order_id = self.get_payment_order_id()
		return frappe.db.exists("Razorpay Order", {"order_id": order_id})

	def get_payment_order_id(self) -> str:
		if self.payload.get("payment"):
			return self.payload.get("payment").get("entity", {}).get("order_id")

	def get_subscription_id(self) -> str:
		if self.payload.get("subscription"):
			return self.payload.get("subscription").get("entity", {}).get("id")
