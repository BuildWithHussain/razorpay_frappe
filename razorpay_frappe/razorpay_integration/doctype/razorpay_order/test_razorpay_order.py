# Copyright (c) 2024, Build With Hussain and Contributors
# See license.txt

from urllib.parse import urljoin

import frappe
from frappe.tests.test_api import FrappeAPITestCase

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)


class TestRazorpayOrder(FrappeAPITestCase):
	def test_order_creation_endpoint(self):
		test_amount = 200
		data = self.initiate_test_order(test_amount)

		self.assertIn("key_id", data)
		self.assertIn("order_id", data)

		# order doc created behind the scenes
		order_doc_exists = frappe.db.exists(
			"Razorpay Order", {"order_id": data.get("order_id")}
		)
		self.assertTrue(order_doc_exists)

		# status should be pending
		order_doc = frappe.get_doc(
			"Razorpay Order", {"order_id": data.get("order_id")}
		)
		self.assertEqual(order_doc.status, "Pending")
		self.assertEqual(order_doc.amount, test_amount)

	def test_success_handler(self):
		data = RazorpayOrder.create(200)
		rzp_order_id = data.get("order_id")

		frappe.form_dict = {
			"order_id": rzp_order_id,
			"payment_id": "xyz",
			"signature": "abc",
		}
		RazorpayOrder.handle_success()
		doc = frappe.get_doc("Razorpay Order", {"order_id": rzp_order_id})
		self.assertEqual(doc.status, "Captured")

	def initiate_test_order(self, amount: int, currency: str = "INR"):
		response = self.post(
			self.get_path("initiate-order"),
			{"amount": amount, "currency": currency},
		)
		return response.json.get("data")

	def test_failure_handler(self):
		data = RazorpayOrder.create(200)
		rzp_order_id = data.get("order_id")

		frappe.form_dict = {"order_id": rzp_order_id}
		RazorpayOrder.handle_failure()
		doc = frappe.get_doc("Razorpay Order", {"order_id": rzp_order_id})
		self.assertEqual(doc.status, "Failed")

	def get_path(self, *parts):
		return urljoin(self.site_url, "/".join(("razorpay-api", *parts)))
