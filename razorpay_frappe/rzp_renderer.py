from enum import StrEnum

import frappe
from frappe.utils.response import build_response
from werkzeug.wrappers import Response

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.utils import verify_webhook_signature


class Endpoints(StrEnum):
	SUCCESS_HANDLER = "success-handler"
	FAILURE_HANDLER = "failure-handler"
	WEBHOOK_HANDLER = "webhook-handler"
	INITIATE_ORDER = "initiate-order"


class RazorpayEndpointHandler:
	def __init__(self, path: str, status_code: int | None = None):
		self.path = path
		self.request_obj = frappe.request
		self.endpoint: Endpoints = None

	def can_render(self) -> bool:
		if not self.path.startswith("razorpay/"):
			return False

		parts = self.path.split("/")
		if len(parts) < 2:
			return False

		endpoint = parts[1]
		if endpoint in set(Endpoints):
			self.endpoint = endpoint
			return True

		return False

	def render(self) -> Response:
		response = None

		if self.endpoint == Endpoints.INITIATE_ORDER:
			response = RazorpayOrder.initiate()

		elif self.endpoint == Endpoints.FAILURE_HANDLER:
			response = RazorpayOrder.handle_failure()

		elif self.endpoint == Endpoints.WEBHOOK_HANDLER:
			response = self.handle_webhook()

		elif self.endpoint == Endpoints.SUCCESS_HANDLER:
			response = RazorpayOrder.handle_success()

		frappe.response["data"] = response
		return build_response("json")

	def handle_webhook(self):
		form_dict = frappe.local.form_dict
		payload = frappe.request.get_data()

		verify_webhook_signature(payload)

		current_user = frappe.session.user
		frappe.set_user("Administrator")

		payment_entity = form_dict["payload"]["payment"]["entity"]
		razorpay_order_id = payment_entity["order_id"]
		razorpay_payment_id = payment_entity["id"]
		customer_email = payment_entity["email"]
		event = form_dict.get("event")

		frappe.get_doc(
			{
				"doctype": "Razorpay Webhook Log",
				"event": event,
				"order_id": razorpay_order_id,
				"payment_id": razorpay_payment_id,
				"payload": frappe.as_json(form_dict, indent=2),
			}
		).insert().submit()

		order_exists = frappe.db.exists(
			"Razorpay Order", {"order_id": razorpay_order_id}
		)

		if not order_exists:
			return

		order_doc = frappe.get_doc(
			"Razorpay Order", {"order_id": razorpay_order_id}
		)

		if event == "payment.captured" and not order_doc.status != "Captured":
			order_doc.status = "Captured"
		elif event == "refund.processed" and not order_doc.status == "Refunded":
			refund_entity = form_dict["payload"]["refund"]["entity"]
			order_doc.status = "Refunded"
			order_doc.refund_id = refund_entity["id"]

		order_doc.customer_email = customer_email
		order_doc.save()

		frappe.set_user(current_user)
