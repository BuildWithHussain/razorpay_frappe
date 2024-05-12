<template>
	<RazorpayHeadlessCheckout ref="rzpCheckout" />
	<div class="max-w-3xl py-12 mx-auto">
		<Card title="Checkout with Razorpay">
			<Button
				@click="initiateRazorpayOrder"
				:loading="rzpCheckout?.resource.loading"
				variant="solid"
				theme="gray"
			>
				Pay ₹200
			</Button>
		</Card>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Card } from "frappe-ui";
import RazorpayHeadlessCheckout from "./RazorpayHeadlessCheckout.vue";

const rzpCheckout = ref(null);

function initiateRazorpayOrder() {
	const options = {
		amount: 200,
		currency: "INR",
		meta_data: {
			"order-for": "a fake apple watch",
		},
		onSuccess() {
			alert("Payment Successful!");
		},
		onFailure() {
			alert("Payment Failed!");
		},
	};
	rzpCheckout?.value.createOrder(options);
}
</script>
