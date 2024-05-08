from enum import StrEnum

import frappe
from werkzeug.wrappers import Response


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
		return Response("Yup, it will be handled!")
