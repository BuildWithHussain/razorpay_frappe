<!-- This example uses FrappeUI's Resource Manager for AJAX calls -->
<template></template>

<script setup>
import { ref, onMounted } from "vue";
import { createResource } from "frappe-ui";

const successCallback = ref(null);
const failureCallback = ref(null);

const CHECKOUT_JS_SRC = "https://checkout.razorpay.com/v1/checkout.js";

onMounted(() => {
	if (!isRazorpayCheckoutJSLoaded()) {
		loadRazorpayCheckoutJS();
	}
});

function handlePaymentSuccess(response) {
	createResource({
		url: "/razorpay-api/success-handler",
		auto: true,
		makeParams() {
			return {
				order_id: response.razorpay_order_id,
				payment_id: response.razorpay_payment_id,
				signature: response.razorpay_signature,
			};
		},
		onSuccess() {
			if (successCallback.value) {
				successCallback.value(response);
			}
		},
	});
}

function handlePaymentFailed(response) {
	if (failureCallback.value) {
		failureCallback.value(response);
	}

	createResource({
		url: "/razorpay-api/failure-handler",
		auto: true,
		makeParams() {
			return {
				order_id: response.error.metadata.order_id,
			};
		},
	});
}

const createRazorpayOrderResource = createResource({
	url: "/razorpay-api/initiate-order",
	onSuccess(data) {
		console.log(data);
		const orderId = data.order_id;
		const razorpayKey = data.key_id;

		const options = {
			key: razorpayKey,
			name: "Razorpay Frappe",
			description: "Sample Checkout",
			order_id: orderId,
			handler: handlePaymentSuccess,
			theme: {
				color: "#1e1e1e",
			},
		};

		const rzp = new Razorpay(options);
		rzp.on("payment.failed", handlePaymentFailed);
		rzp.open();
	},
});

function isRazorpayCheckoutJSLoaded() {
	const scripts = document.getElementsByTagName("script");

	for (let script of scripts) {
		if (script.getAttribute("src") === CHECKOUT_JS_SRC) {
			return true;
		}
	}

	return false;
}

function loadRazorpayCheckoutJS() {
	let razorpayScript = document.createElement("script");
	razorpayScript.setAttribute("src", CHECKOUT_JS_SRC);
	document.head.appendChild(razorpayScript);
}

const createRazorpayOrder = (options) => {
	successCallback.value = options.onSuccess;
	failureCallback.value = options.onFailure;

	createRazorpayOrderResource.fetch({
		amount: options["amount"],
		currency: options.currency || "INR",
		ref_dt: options.ref_dt,
		ref_dn: options.ref_dn,
		meta_data: options.meta_data,
	});
};

defineExpose({
	createOrder: createRazorpayOrder,
	resource: createRazorpayOrderResource,
});
</script>
