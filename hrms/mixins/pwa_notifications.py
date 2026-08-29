# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import bold


class PWANotificationsMixin:
	"""Mixin class for managing PWA updates"""

	APPROVAL_STATUS_FIELD = {
		"Leave Application": "status",
		"Expense Claim": "approval_status",
		"Shift Request": "status",
		"Attendance Request": "workflow_state",
		"Employee Advance": "workflow_state",
	}

	APPROVER_FIELDS = {
		"Leave Application": ["leave_approver"],
		"Expense Claim": ["expense_approver"],
		"Shift Request": ["approver"],
		"Attendance Request": ["custom_attendance_request_approver"],
		"Employee Advance": ["custom_advance_approver", "custom_accountant"],
	}

	def notify_approval_status(self):
		"""Send approval status notification - to employee"""
		status_field = self._get_doc_status_field()
		status = self.get(status_field)

		if self.has_value_changed(status_field) and status in ["Approved", "Rejected"]:
			from_user = frappe.session.user
			from_user_name = self._get_user_name(from_user)
			to_user = self._get_employee_user()

			if not to_user or from_user == to_user:
				return

			notification = frappe.new_doc("PWA Notification")
			notification.from_user = from_user
			notification.to_user = to_user
			notification.message = (
				f"{bold('Your')} {bold(self.doctype)} {self.name} "
				f"has been {bold(status)} by {bold(from_user_name)}"
			)
			notification.reference_document_type = self.doctype
			notification.reference_document_name = self.name
			notification.insert(ignore_permissions=True)

	def notify_approver(self):
		"""Send new request notification - to all configured approvers"""
		from_user = self._get_employee_user()
		approvers = self._get_doc_approvers()

		for to_user in approvers:
			if not to_user or from_user == to_user:
				continue

			notification = frappe.new_doc("PWA Notification")
			notification.message = (
				f"{bold(self.employee_name)} raised a new "
				f"{bold(self.doctype)} for approval: {self.name}"
			)
			notification.from_user = from_user
			notification.to_user = to_user
			notification.reference_document_type = self.doctype
			notification.reference_document_name = self.name
			notification.insert(ignore_permissions=True)

	def _get_doc_status_field(self) -> str:
		return self.APPROVAL_STATUS_FIELD[self.doctype]

	def _get_doc_approvers(self) -> list:
		"""Return all configured approver user IDs for this document"""
		fieldnames = self.APPROVER_FIELDS.get(self.doctype, [])
		approvers = [self.get(fieldname) for fieldname in fieldnames]
		return self._remove_duplicate_users(approvers)

	def _remove_duplicate_users(self, users) -> list:
		"""Remove empty and duplicate users while preserving order"""
		result = []
		seen = set()
		for user in users or []:
			if user and user not in seen:
				result.append(user)
				seen.add(user)
		return result

	def _get_employee_user(self) -> str:
		return frappe.db.get_value("Employee", self.employee, "user_id", cache=True)

	def _get_user_name(self, user) -> str:
		return frappe.db.get_value("User", user, "full_name", cache=True)
