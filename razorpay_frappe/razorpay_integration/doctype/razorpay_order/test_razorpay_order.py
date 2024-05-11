# Copyright (c) 2024, Build With Hussain and Contributors
# See license.txt

import frappe
from frappe.tests.test_api import FrappeAPITestCase

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.rzp_renderer import Endpoints


class TestRazorpayOrder(FrappeAPITestCase):
	def test_order_creation(self):
		test_amount = 200
		data = RazorpayOrder.initiate(200)

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
		data = RazorpayOrder.initiate(200)
		rzp_order_id = data.get("order_id")

		RazorpayOrder.handle_success(rzp_order_id, "abc", "xyz")

		doc = frappe.get_doc("Razorpay Order", {"order_id": rzp_order_id})
		self.assertEqual(doc.status, "Captured")

	def test_failure_handler(self):
		data = RazorpayOrder.initiate(200)
		rzp_order_id = data.get("order_id")

		RazorpayOrder.handle_failure(rzp_order_id)

		doc = frappe.get_doc("Razorpay Order", {"order_id": rzp_order_id})
		self.assertEqual(doc.status, "Failed")

	def test_guest_checkout_disabled_with_guest(self):
		doc = frappe.get_doc("Razorpay Settings")
		doc.allow_guest_checkout = 0
		doc.save()
		frappe.db.commit()

		response = self.post(
			f"{self.site_url}/razorpay-api/{Endpoints.INITIATE_ORDER}",
			{"amount": 200},
		)
		self.assertEqual(response.status_code, 403)

	def test_guest_checkout_enabled_with_user(self):
		doc = frappe.get_doc("Razorpay Settings")
		doc.allow_guest_checkout = 0
		doc.save()
		frappe.db.commit()

		# login as user
		response = self.post(
			f"{self.site_url}/razorpay-api/initiate-order",
			{"amount": 200, "sid": self.sid},
		)
		self.assertEqual(response.status_code, 200)

	def test_guest_checkout_enabled(self):
		doc = frappe.get_doc("Razorpay Settings")
		doc.allow_guest_checkout = 1
		doc.save()
		frappe.db.commit()

		response = self.post(
			f"{self.site_url}/razorpay-api/initiate-order", {"amount": 200}
		)

		self.assertEqual(response.status_code, 200)
