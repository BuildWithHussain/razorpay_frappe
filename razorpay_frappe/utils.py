import os
from enum import StrEnum

import frappe
import razorpay
from frappe.utils.password import get_decrypted_password


class RazorpayPaymentWebhookEvents(StrEnum):
	PaymentCaptured = "payment.captured"
	RefundProcessed = "refund.processed"


class RazorpaySubscriptionWebhookEvents(StrEnum):
	SubscriptionActivated = "subscription.activated"
	SubscriptionCharged = "subscription.charged"
	SubscriptionCompleted = "subscription.completed"
	SubscriptionUpdated = "subscription.updated"
	SubscriptionPending = "subscription.pending"
	SubscriptionHalted = "subscription.halted"
	SubscriptionCancelled = "subscription.cancelled"
	SubscriptionPaused = "subscription.paused"
	SubscriptionResumed = "subscription.resumed"


def get_razorpay_client():
    in_ci = os.environ.get("CI")
    if not in_ci:
        razorpay_settings = frappe.get_cached_doc(
            "Razorpay Settings"
        )
        key_id = getattr(
            razorpay_settings,
            "api_key",
            None
        ) or getattr(
            razorpay_settings,
            "key_id",
            None
        )
        key_secret = razorpay_settings.get_password(
            "api_secret", raise_exception=False
        ) or razorpay_settings.get_password(
            "key_secret", raise_exception=False
        )
    else:
        key_id = os.environ.get(
            "RZP_SANDBOX_KEY_ID"
        )
        key_secret = os.environ.get(
            "RZP_SANDBOX_KEY_SECRET"
        )
    if not (key_id and key_secret):
        frappe.throw(
            f"Please set API keys in "
            f"{frappe.bold('Razorpay Settings')} "
            f"before trying to create a razorpay client!"
        )
    return razorpay.Client(
        auth=(key_id, key_secret)
    )


def get_in_razorpay_money(amount: int) -> int:
	return amount * 100


def convert_from_razorpay_money(amount: int) -> int:
	return amount / 100


def verify_webhook_signature(payload):
	signature = frappe.get_request_header("X-Razorpay-Signature")
	webhook_secret = get_decrypted_password(
		"Razorpay Settings", "Razorpay Settings", "webhook_secret"
	)

	client = get_razorpay_client()
	client.utility.verify_webhook_signature(
		payload.decode(), signature, webhook_secret
	)
