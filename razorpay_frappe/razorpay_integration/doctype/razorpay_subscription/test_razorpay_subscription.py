# Copyright (c) 2024, Build With Hussain and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from razorpay_frappe.rzp_renderer import RazorpayEndpointHandler


class TestRazorpaySubscription(FrappeTestCase):
	def setUp(self):
		self.test_plan = frappe.get_doc(
			{
				"doctype": "Razorpay Plan",
				"period": "Monthly",
				"interval": 1,
				"item_name": "Test Monthly Plan",
				"item_amount": 100,
			}
		).insert()

		self.test_subscription = frappe.get_doc(
			{
				"doctype": "Razorpay Subscription",
				"plan_id": self.test_plan.name,
				"total_count": 12,
			}
		).insert()

	def test_handle_cancelled_webhook(self):
		self.trigger_webhook_handler_with_sample_payload(
			"subscription.cancelled"
		)

		subscription_status, ended_at = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			["status", "ended_at"],
		)

		self.assertEqual(subscription_status, "Cancelled")
		self.assertEqual(str(ended_at), "2019-09-05")

	def test_handle_authenticated_webhook(self):
		self.trigger_webhook_handler_with_sample_payload(
			"subscription.authenticated"
		)

		status, customer_id = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			["status", "customer_id"],
		)

		self.assertEqual(status, "Authenticated")
		self.assertEqual(customer_id, "CUSTOMER-ID")

	def test_handle_completed_webhook(self):
		self.trigger_webhook_handler_with_sample_payload(
			"subscription.completed"
		)

		status, ended_at = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			["status", "ended_at"],
		)

		self.assertEqual(status, "Completed")
		self.assertEqual(str(ended_at), "2020-09-04")

	def test_activated_no_upfront_webhook(self):
		self.trigger_webhook_handler_with_sample_payload(
			"subscription.activated.no_upfront"
		)

		status = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			"status",
		)

		self.assertEqual(status, "Active")

	def test_activated_with_upfront_charge_webhook(self):
		self.trigger_webhook_handler_with_sample_payload(
			"subscription.activated.with_upfront"
		)

		status = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			"status",
		)
		self.assertEqual(status, "Active")

		charge_order = frappe.db.exists(
			"Razorpay Order",
			{
				"subscription": self.test_subscription.name,
				"type": "Subscription",
				"order_id": "test_subscription_upfront_order_id",
				"payment_id": "test_subscription_upfront_payment_id",
				"invoice_id": "test_subscription_upfront_invoice_id",
				"status": "Paid",
			},
		)
		self.assertIsNotNone(charge_order)

	def test_subscription_charged_webhook(self):
		self.trigger_webhook_handler_with_sample_payload("subscription.charged")

		status = frappe.db.get_value(
			"Razorpay Subscription",
			self.test_subscription.name,
			"status",
		)
		self.assertEqual(status, "Active")

		charge_order = frappe.db.exists(
			"Razorpay Order",
			{
				"subscription": self.test_subscription.name,
				"type": "Subscription",
				"order_id": "test_subscription_charged_order_id",
				"payment_id": "test_subscription_charged_payment_id",
				"invoice_id": "test_subscription_charged_invoice_id",
				"status": "Paid",
			},
		)
		self.assertIsNotNone(charge_order)

	def trigger_webhook_handler_with_sample_payload(self, event: str):
		webhook_payload = process_payload_string(
			SAMPLE_WEBHOOK_PAYLOADS[event],
			self.test_subscription.id,
		)

		RazorpayEndpointHandler(
			"razorpay-api/webhook-handler"
		).create_webhook_log(webhook_payload)


def process_payload_string(webhook_payload, subscription_id):
	return frappe.parse_json(
		webhook_payload.replace("<SUBSCRIPTION-ID>", subscription_id)
	)


SAMPLE_WEBHOOK_PAYLOADS = {
	"subscription.authenticated": """
{
  "entity": "event",
  "account_id": "acc_F5Motm2sJ5Fomd",
  "event": "subscription.authenticated",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_F5Zu0nrXVhHV2m",
        "customer_id": "CUSTOMER-ID",
        "status": "authenticated",
        "current_start": null,
        "current_end": null,
        "ended_at": null,
        "quantity": 1,
        "notes": [],
        "charge_at": 1593109800,
        "start_at": 1593109800,
        "end_at": 1598380200,
        "auth_attempts": 0,
        "total_count": 3,
        "paid_count": 0,
        "customer_notify": true,
        "created_at": 1592811228,
        "expire_by": null,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 3
      }
    }
  },
  "created_at": 1592811255
}
""",
	"subscription.activated.no_upfront": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.activated",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "active",
        "current_start": 1570213800,
        "current_end": 1572892200,
        "ended_at": null,
        "quantity": 1,
        "notes": {
          "notes_key_1": "Tea, Earl Grey, Hot",
          "notes_key_2": "Tea, Earl Grey… decaf."
        },
        "charge_at": 1570213800,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 0,
        "total_count": 12,
        "paid_count": 0,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 11
      }
    }
  },
  "created_at": 1567690383
}
""",
	"subscription.activated.with_upfront": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.activated",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "active",
        "type": 2,
        "current_start": 1570213800,
        "current_end": 1572892200,
        "ended_at": null,
        "quantity": 1,
        "notes": {
          "notes_key_1": "Tea, Earl Grey, Hot",
          "notes_key_2": "Tea, Earl Grey… decaf."
        },
        "charge_at": 1570213800,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 0,
        "total_count": 12,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 11
      }
    },
    "payment": {
      "entity": {
        "id": "test_subscription_upfront_payment_id",
        "entity": "payment",
        "amount": 100000,
        "currency": "INR",
        "status": "captured",
        "order_id": "test_subscription_upfront_order_id",
        "invoice_id": "test_subscription_upfront_invoice_id",
        "international": false,
        "method": "card",
        "amount_refunded": 0,
        "amount_transferred": 0,
        "refund_status": null,
        "captured": "1",
        "description": "Recurring Payment via Subscription",
        "card_id": "card_DEXFX0KGtXexrH",
        "card": {
          "id": "card_DEXFX0KGtXexrH",
          "entity": "card",
          "name": "Gaurav Kumar",
          "last4": "5558",
          "network": "MasterCard",
          "type": "credit",
          "issuer": "KARB",
          "international": false,
          "emi": false,
          "expiry_month": 2,
          "expiry_year": 2022
        },
        "bank": null,
        "wallet": null,
        "vpa": null,
        "email": "gaurav.kumar@example.com",
        "contact": "+919876543210",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "token_id": null,
        "notes": [],
        "fee": 2900,
        "tax": 0,
        "error_code": null,
        "error_description": null,
        "created_at": 1567690382
      }
    },
    "created_at": 1567690383
  }
}
""",
	"subscription.charged": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.charged",
  "contains": [
    "subscription",
    "payment"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "active",
        "type": 2,
        "current_start": 1570213800,
        "current_end": 1572892200,
        "ended_at": null,
        "quantity": 1,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": 1572892200,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 0,
        "total_count": 12,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 11
      }
    },
    "payment": {
      "entity": {
        "id": "test_subscription_charged_payment_id",
        "entity": "payment",
        "amount": 100000,
        "currency": "INR",
        "status": "captured",
        "order_id": "test_subscription_charged_order_id",
        "invoice_id": "test_subscription_charged_invoice_id",
        "international": false,
        "method": "card",
        "amount_refunded": 0,
        "amount_transferred": 0,
        "refund_status": null,
        "captured": "1",
        "description": "Recurring Payment via Subscription",
        "card_id": "card_DEXFX0KGtXexrH",
        "card": {
          "id": "card_DEXFX0KGtXexrH",
          "entity": "card",
          "name": "Gaurav Kumar",
          "last4": "5558",
          "network": "MasterCard",
          "type": "credit",
          "issuer": "KARB",
          "international": false,
          "emi": false,
          "expiry_month": 2,
          "expiry_year": 2022
        },
        "bank": null,
        "wallet": null,
        "vpa": null,
        "email": "gaurav.kumar@example.com",
        "contact": "+919876543210",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "token_id": null,
        "notes": [],
        "fee": 2900,
        "tax": 0,
        "error_code": null,
        "error_description": null,
        "created_at": 1567690382
      }
    }
  },
  "created_at": 1567690383
}
""",
	"subscription.completed": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.completed",
  "contains": [
    "subscription",
    "payment"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "completed",
        "type": 2,
        "current_start": 1599244200,
        "current_end": 1601836200,
        "ended_at": 1599244200,
        "quantity": 1,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": null,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 0,
        "total_count": 12,
        "paid_count": 11,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 0
      }
    },
    "payment": {
      "entity": {
        "id": "pay_DEXkZ54GsNwVk9",
        "entity": "payment",
        "amount": 100000,
        "currency": "INR",
        "status": "captured",
        "order_id": "order_DEXkYoCpua7kn3",
        "invoice_id": "inv_DEXkYmFDy966lT",
        "international": false,
        "method": "card",
        "amount_refunded": 0,
        "amount_transferred": 0,
        "refund_status": null,
        "captured": "1",
        "description": "Recurring Payment via Subscription",
        "card_id": "card_DEXkZBosDfKGEe",
        "card": {
          "id": "card_DEXkZBosDfKGEe",
          "entity": "card",
          "name": "Gaurav Kumar",
          "last4": "0008",
          "network": "MasterCard",
          "type": "unknown",
          "issuer": "",
          "international": false,
          "emi": false,
          "expiry_month": 11,
          "expiry_year": 2031
        },
        "bank": null,
        "wallet": null,
        "vpa": null,
        "email": "gaurav.kumar@example.com",
        "contact": "+919876543210",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "token_id": null,
        "notes": [],
        "fee": 2900,
        "tax": 0,
        "error_code": null,
        "error_description": null,
        "created_at": 1567692144
      }
    }
  },
  "created_at": 1567692150
}
""",
	"subscription.updated": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.updated",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "sub_DEXpmJhEIZK4fe",
        "entity": "subscription",
        "plan_id": "plan_BvrHngQ0xLNnNG",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "active",
        "type": 3,
        "current_start": 1567692455,
        "current_end": 1570213800,
        "ended_at": null,
        "quantity": 4,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": 1570213800,
        "start_at": 1567692455,
        "end_at": 1599071400,
        "auth_attempts": 0,
        "total_count": 53,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1567692440,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 52
      }
    }
  },
  "created_at": 1567692560
}
""",
	"subscription.pending": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.pending",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "sub_DEX6xcJ1HSW4CR",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "pending",
        "type": 2,
        "current_start": 1572892200,
        "current_end": 1575484200,
        "ended_at": null,
        "quantity": 1,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": 1572978600,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 1,
        "total_count": 12,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 10
      }
    }
  },
  "created_at": 1567691026
}
""",
	"subscription.halted": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.halted",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "sub_DEX6xcJ1HSW4CR",
        "entity": "subscription",
        "plan_id": "plan_BvrFKjSxauOH7N",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "halted",
        "type": 2,
        "current_start": 1572892200,
        "current_end": 1575484200,
        "ended_at": null,
        "quantity": 1,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": 1575484200,
        "start_at": 1570213800,
        "end_at": 1599244200,
        "auth_attempts": 4,
        "total_count": 12,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1567689895,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 10
      }
    }
  },
  "created_at": 1567691269
}
""",
	"subscription.paused": """
{
  "entity": "event",
  "account_id": "acc_Fe3fPCmiStazv3",
  "event": "subscription.paused",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "sub_FeQ9WWOjGUZMpG",
        "entity": "subscription",
        "plan_id": "plan_FeMmuaVVa1HR0W",
        "customer_id": "cust_FeOEa4PPa0by07",
        "status": "paused",
        "type": 1,
        "current_start": 1600416437,
        "current_end": 1602959400,
        "ended_at": null,
        "quantity": 1,
        "notes": [],
        "charge_at": null,
        "start_at": 1600416437,
        "end_at": 1610908200,
        "auth_attempts": 0,
        "total_count": 5,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1600416405,
        "expire_by": null,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "payment_method": "card",
        "remaining_count": 4,
        "pause_initiated_by": "self",
        "cancel_initiated_by": null
      }
    }
  },
  "created_at": 1600416473
}
""",
	"subscription.resumed": """
{
  "entity": "event",
  "account_id": "acc_Fe3fPCmiStazv3",
  "event": "subscription.resumed",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "sub_FeQ9WWOjGUZMpG",
        "entity": "subscription",
        "plan_id": "plan_FeMmuaVVa1HR0W",
        "customer_id": "cust_FeOEa4PPa0by07",
        "status": "active",
        "type": 1,
        "current_start": 1600416437,
        "current_end": 1602959400,
        "ended_at": null,
        "quantity": 1,
        "notes": [],
        "charge_at": 1602959400,
        "start_at": 1600416437,
        "end_at": 1610908200,
        "auth_attempts": 0,
        "total_count": 5,
        "paid_count": 1,
        "customer_notify": true,
        "created_at": 1600416405,
        "expire_by": null,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "payment_method": "card",
        "remaining_count": 4,
        "pause_initiated_by": null,
        "cancel_initiated_by": null
      }
    }
  },
  "created_at": 1600416481
}
""",
	"subscription.cancelled": """
{
  "entity": "event",
  "account_id": "acc_BFQ7uQEaa7j2z7",
  "event": "subscription.cancelled",
  "contains": [
    "subscription"
  ],
  "payload": {
    "subscription": {
      "entity": {
        "id": "<SUBSCRIPTION-ID>",
        "entity": "subscription",
        "plan_id": "plan_BvrHngQ0xLNnNG",
        "customer_id": "cust_C0WlbKhp3aLA7W",
        "status": "cancelled",
        "type": 3,
        "current_start": 1568226600,
        "current_end": 1568831400,
        "ended_at": 1567692729,
        "quantity": 4,
        "notes": {
          "Important": "Notes for Internal Reference"
        },
        "charge_at": null,
        "start_at": 1567692455,
        "end_at": 1599071400,
        "auth_attempts": 0,
        "total_count": 53,
        "paid_count": 2,
        "customer_notify": true,
        "created_at": 1567692440,
        "expire_by": 1567881000,
        "short_url": null,
        "has_scheduled_changes": false,
        "change_scheduled_at": null,
        "source": "api",
        "offer_id":"offer_JHD834hjbxzhd38d",
        "remaining_count": 51
      }
    }
  },
  "created_at": 1567692732
}
""",
}
