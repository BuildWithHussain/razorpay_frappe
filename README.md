### Razorpay Integration for your custom Apps


![Server Tests](https://github.com/BuildWithHussain/razorpay_frappe/actions/workflows/ci.yml/badge.svg)

## Introduction

I never want to write Razorpay Integration in my custom app again!

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site $SITE_NAME install-app razorpay_frappe
```

## Usage

Just install this app, put your credentials in `Razorpay Settings` (Single Doctype) and your payment backend should be ready to go!

## Integrating in Custom App

There is only 1 master doctype in this app: `Razorpay Order`

This app brings in 3 API endpoints for handling this order:

1. "/razorpay-api/initiate-order"

2. "/razorpay-api/success-handler"

3. "/razorpay-api/failure-handler"

### Guest Checkout

By default, guest checkout is enabled in the settings, which means these endpoints

### Webhook Setup


## Frontend Integration

You can find two examples with this repo:

1. Portal Page with VanillaJS ([source](./examples/checkout.html))
2. FrappeUI Page with Vue Headless component ([source](./examples/FrappeUICheckout.vue))

The nice thing about the second example is that you can just copy the `RazorpayHeadlessCheckout` ([source](./examples/RazorpayHeadlessCheckout.vue)) component to your FrappeUI based frontend and it will just work!

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/razorpay_frappe
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
