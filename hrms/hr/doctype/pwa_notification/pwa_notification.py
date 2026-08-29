# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import hrms


class PWANotification(Document):
	def on_update(self):
		hrms.refetch_resource("hrms:notifications", self.to_user)

	def after_insert(self):
		self.send_push_notification()

	def send_push_notification(self):
		try:
			from frappe.push_notification import PushNotification

			push_notification = PushNotification("hrms")
			if push_notification.is_enabled():
				push_notification.send_notification_to_user(
					self.to_user,
					self.reference_document_type,
					self.message,
					link=self.get_notification_link(),
					icon=f"{frappe.utils.get_url()}/assets/hrms/manifest/favicon-196.png",
				)
		except ImportError:
			# push notifications are not supported in the current framework version
			pass
		except Exception:
			self.log_error(f"Error sending push notification: {self.name}")

	def get_notification_link(self):
		base_url = f"{frappe.utils.get_url()}/hrms"

		route_map = {
			"Leave Application": "leave-applications",
			"Expense Claim": "expense-claims",
			"Attendance Request": "attendance-requests",
			"Employee Advance": "employee-advances",
		}

		path = route_map.get(self.reference_document_type)
		if path:
			return f"{base_url}/{path}/{self.reference_document_name}"

		return base_url
