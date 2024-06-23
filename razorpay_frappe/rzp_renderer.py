from enum import StrEnum

import frappe
from frappe.utils.response import build_response
from werkzeug.wrappers import Response

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.utils import (
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
			ref_dt = frappe.form_dict.get("ref_dt")
			ref_dn = frappe.form_dict.get("ref_dn")

			response = RazorpayOrder.initiate(
				amount, currency, meta_data, ref_dt=ref_dt, ref_dn=ref_dn
			)

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
		self.create_webhook_log(form_dict)

	def create_webhook_log(self, payload: dict):
		current_user = frappe.session.user
		frappe.set_user("Administrator")

		event = payload.get("event")
		frappe.get_doc(
			{
				"doctype": "Razorpay Webhook Log",
				"event": event,
				"payload": frappe.as_json(payload, indent=2),
			}
		).insert().submit()

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
