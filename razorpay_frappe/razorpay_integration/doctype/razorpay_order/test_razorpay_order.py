# Copyright (c) 2024, Build With Hussain and Contributors
# See license.txt

import frappe
from frappe.tests.test_api import FrappeAPITestCase

from razorpay_frappe.razorpay_integration.doctype.razorpay_order.razorpay_order import (
	RazorpayOrder,
)
from razorpay_frappe.rzp_renderer import Endpoints, RazorpayEndpointHandler


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
		self.assertEqual(doc.status, "Paid")

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
			f"{self.site_url}/razorpay-api/{Endpoints.INITIATE_ORDER}",
			{"amount": 200, "sid": self.sid},
		)
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.json.get("message").get("order_id"))
		self.assertIsNotNone(response.json.get("message").get("key_id"))

	def test_guest_checkout_enabled(self):
		doc = frappe.get_doc("Razorpay Settings")
		doc.allow_guest_checkout = 1
		doc.save()
		frappe.db.commit()

		response = self.post(
			f"{self.site_url}/razorpay-api/{Endpoints.INITIATE_ORDER}",
			{"amount": 200},
		)

		self.assertEqual(response.status_code, 200)

	def test_webhook_handler_payment_captured(self):
		order_id = RazorpayOrder.initiate(200).get("order_id")

		# webhook received
		webhook_payload = get_test_webhook_payload(order_id)

		RazorpayEndpointHandler(
			"razorpay-api/webhook-handler"
		).create_webhook_log(webhook_payload)

		# order status is paid
		status = frappe.db.get_value(
			"Razorpay Order", {"order_id": order_id}, "status"
		)
		self.assertEqual(status, "Paid")


def get_test_webhook_payload(
	order_id: str, event: str = "payment.captured"
) -> dict:
	payload_json = """
	{
	"account_id": "acc_7HIbgUNYLcDKI9",
	"contains": [
		"payment"
	],
	"created_at": 1715397833,
	"entity": "event",
	"event": "<EVENT>",
	"payload": {
		"payment": {
		"entity": {
			"acquirer_data": {
			"rrn": "449800533051"
			},
			"amount": 110000,
			"amount_refunded": 0,
			"amount_transferred": 0,
			"bank": null,
			"base_amount": 110000,
			"captured": true,
			"card_id": null,
			"contact": "+918654578475",
			"created_at": 1715397821,
			"currency": "INR",
			"description": "FOSS United Event",
			"email": "void@razorpay.com",
			"entity": "payment",
			"error_code": null,
			"error_description": null,
			"error_reason": null,
			"error_source": null,
			"error_step": null,
			"fee": 2596,
			"id": "pay_O92LqAmeiTCeG2",
			"international": false,
			"invoice_id": null,
			"method": "upi",
			"notes": [],
			"order_id": "<ORDER-ID>",
			"provider": null,
			"refund_status": null,
			"reward": null,
			"status": "captured",
			"tax": 396,
			"upi": {
			"payer_account_type": "bank_account",
			"vpa": "xxx@paytm"
			},
			"vpa": "xxx@paytm",
			"wallet": null
		}
		}
	}
	}
	"""

	payload_json = payload_json.replace("<ORDER-ID>", order_id)
	payload_json = payload_json.replace("<EVENT>", event)

	return frappe.parse_json(payload_json)
