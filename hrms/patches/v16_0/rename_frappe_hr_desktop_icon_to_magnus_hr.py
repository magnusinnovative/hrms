import json
import os

import frappe

OLD_LABEL = "Frappe HR"
NEW_LABEL = "Magnus HR"
HR_HOME = "/desk/hr-setup"


def execute():
	"""Show HR as a "Magnus HR" folder on the desk, like the pre-16.52 desktop.

	Frappe 16.52 no longer imports `desktop_icon/*.json` on migrate, so the rename has to be done
	on the records. Plain SQL is used on purpose: Desktop Icon's rename/update hooks rewrite or
	delete those JSON files in developer mode.
	"""
	rename_app_icon()
	create_missing_icons_from_files()
	rename_in_user_layouts()

	# Render the desk as the Desktop Icons grid (folders) instead of the Apps screen.
	frappe.db.set_single_value("Desktop Settings", "desktop_page", "Desktop Icons")

	from frappe.desk.doctype.desktop_icon.desktop_icon import clear_every_users_desktop_icons

	clear_every_users_desktop_icons()


def rename_app_icon():
	if frappe.db.exists("Desktop Icon", OLD_LABEL):
		if frappe.db.exists("Desktop Icon", NEW_LABEL):
			frappe.db.delete("Desktop Icon", {"name": OLD_LABEL})
		else:
			frappe.db.sql(
				"update `tabDesktop Icon` set name=%s, label=%s where name=%s",
				(NEW_LABEL, NEW_LABEL, OLD_LABEL),
			)

	if frappe.db.exists("Desktop Icon", NEW_LABEL):
		frappe.db.sql(
			"update `tabDesktop Icon` set label=%s, link=%s, link_type='External' where name=%s",
			(NEW_LABEL, HR_HOME, NEW_LABEL),
		)

	# child workspaces (Leaves, Payroll, ...) point to the folder by label
	frappe.db.sql(
		"update `tabDesktop Icon` set parent_icon=%s where parent_icon=%s",
		(NEW_LABEL, OLD_LABEL),
	)
	# role restrictions on the icon, if any
	frappe.db.sql(
		"update `tabHas Role` set parent=%s where parenttype='Desktop Icon' and parent=%s",
		(NEW_LABEL, OLD_LABEL),
	)


def create_missing_icons_from_files():
	"""Create any HR desktop icon that the site does not have yet, from hrms/desktop_icon."""
	folder = frappe.get_app_path("hrms", "desktop_icon")
	if not os.path.isdir(folder):
		return

	files = sorted(os.listdir(folder), key=lambda f: f != "magnus_hr.json")  # folder icon first
	frappe.flags.in_import = True  # don't let on_update export files back
	try:
		for file in files:
			if not file.endswith(".json"):
				continue
			with open(os.path.join(folder, file)) as f:
				data = json.load(f)
			if frappe.db.exists("Desktop Icon", data.get("name") or data.get("label")):
				continue
			for key in ("creation", "modified", "modified_by", "owner"):
				data.pop(key, None)
			doc = frappe.get_doc(data)
			doc.flags.ignore_links = True
			doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	finally:
		frappe.flags.in_import = False


def rename_in_user_layouts():
	"""Users who rearranged their desk keep a saved layout that names the folder."""
	if not frappe.db.table_exists("Desktop Layout"):
		return

	for row in frappe.get_all("Desktop Layout", fields=["name", "layout"]):
		if row.layout and f'"{OLD_LABEL}"' in row.layout:
			frappe.db.set_value(
				"Desktop Layout",
				row.name,
				"layout",
				row.layout.replace(f'"{OLD_LABEL}"', f'"{NEW_LABEL}"'),
				update_modified=False,
			)
