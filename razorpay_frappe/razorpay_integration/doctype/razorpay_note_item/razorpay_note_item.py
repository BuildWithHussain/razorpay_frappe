# Copyright (c) 2024, Build With Hussain and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RazorpayNoteItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		key: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		value: DF.Data
	# end: auto-generated types

	@staticmethod
	def get_as_dict(notes: list[dict]) -> dict:
		notes_dict = {}
		if not notes:
			return notes_dict

		for note in notes:
			notes_dict[note.key] = note.value

		return notes_dict
