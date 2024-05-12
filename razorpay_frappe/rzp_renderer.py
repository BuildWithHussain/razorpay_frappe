from enum import StrEnum

import frappe
from frappe.utils.response import build_response
from werkzeug.wrappers import Response

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.utils import (
	convert_from_razorpay_money,
	verify_webhook_signature,
)

BASE_API_PATH = "razorpay-api/"


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
		if not self.path.startswith(BASE_API_PATH):
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

		self.check_permissions()

		if self.endpoint == Endpoints.INITIATE_ORDER:
			amount = frappe.form_dict["amount"]
			currency = frappe.form_dict.get("currency", "INR")
			meta_data = frappe.form_dict.get("meta_data")

			response = RazorpayOrder.initiate(amount, currency, meta_data)

		elif self.endpoint == Endpoints.FAILURE_HANDLER:
			order_id = frappe.form_dict["order_id"]
			response = RazorpayOrder.handle_failure(order_id)

		elif self.endpoint == Endpoints.WEBHOOK_HANDLER:
			response = self.handle_webhook()

		elif self.endpoint == Endpoints.SUCCESS_HANDLER:
			order_id = frappe.form_dict["order_id"]
			payment_id = frappe.form_dict["payment_id"]
			signature = frappe.form_dict["signature"]
			response = RazorpayOrder.handle_success(
				order_id, payment_id, signature
			)

		frappe.response["message"] = response
		return build_response("json")

	def handle_webhook(self):
		form_dict = frappe.local.form_dict
		payload = frappe.request.get_data()

		verify_webhook_signature(payload)
		self.process_webhook_payload(form_dict)

	def process_webhook_payload(self, payload: dict):
		current_user = frappe.session.user
		frappe.set_user("Administrator")

		payment_entity = payload["payload"]["payment"]["entity"]
		razorpay_order_id = payment_entity["order_id"]
		razorpay_payment_id = payment_entity["id"]
		customer_email = payment_entity["email"]
		event = payload.get("event")

		frappe.get_doc(
			{
				"doctype": "Razorpay Webhook Log",
				"event": event,
				"order_id": razorpay_order_id,
				"payment_id": razorpay_payment_id,
				"payload": frappe.as_json(payload, indent=2),
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

		if event == "payment.captured" and order_doc.status != "Paid":
			order_doc.status = "Paid"
			order_doc.fee = convert_from_razorpay_money(
				payment_entity.get("fee", 0)
			)
			order_doc.tax = convert_from_razorpay_money(
				payment_entity.get("tax", 0)
			)
			order_doc.method = payment_entity.get("method")
			order_doc.contact = payment_entity.get("contact")
		elif event == "refund.processed" and not order_doc.status == "Refunded":
			refund_entity = payload["payload"]["refund"]["entity"]
			order_doc.status = "Refunded"
			order_doc.refund_id = refund_entity["id"]

		order_doc.customer_email = customer_email
		order_doc.save()

		frappe.set_user(current_user)

	def check_permissions(self):
		settings = frappe.get_cached_doc("Razorpay Settings")

		if self.endpoint == Endpoints.WEBHOOK_HANDLER:
			return

		if not settings.allow_guest_checkout and frappe.session.user == "Guest":
			frappe.throw(
				"You are not permitted to access this endpoint",
				frappe.PermissionError,
			)
