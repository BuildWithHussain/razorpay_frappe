import frappe

doctypes = {
	"Razorpay Settings": "Frappe Razorpay Settings",
}


def execute():
	rename_doctypes()


def rename_doctypes():
	for old in doctypes:
		new = doctypes[old]
		if not frappe.db.exists("DocType", new):
			print(f"Renaming {old} to {new}")
			frappe.rename_doc(
				"DocType", old, new, force=True, ignore_if_exists=True
			)
