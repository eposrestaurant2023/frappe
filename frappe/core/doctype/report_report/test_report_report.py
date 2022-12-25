# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json
import os
import textwrap

import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.custom.doctype.customize_form.customize_form import reset_customization
from frappe.desk.query_report_report import add_total_row, run, save_report_report
from frappe.desk.report_reportview import delete_report_report
from frappe.desk.report_reportview import save_report_report as _save_report_report
from frappe.tests.utils import FrappeTestCase

test_records = frappe.get_test_records("ReportReport")
test_dependencies = ["User"]


class TestReportReport(FrappeTestCase):
	def test_report_report_builder(self):
		if frappe.db.exists("ReportReport", "User Activity ReportReport"):
			frappe.delete_doc("ReportReport", "User Activity ReportReport")

		with open(os.path.join(os.path.dirname(__file__), "user_activity_report_report.json")) as f:
			frappe.get_doc(json.loads(f.read())).insert()

		report_report = frappe.get_doc("ReportReport", "User Activity ReportReport")
		columns, data = report_report.get_data()
		self.assertEqual(columns[0].get("label"), "ID")
		self.assertEqual(columns[1].get("label"), "User Type")
		self.assertTrue("Administrator" in [d[0] for d in data])

	def test_query_report_report(self):
		report_report = frappe.get_doc("ReportReport", "Permitted Documents For User")
		columns, data = report_report.get_data(filters={"user": "Administrator", "doctype": "DocType"})
		self.assertEqual(columns[0].get("label"), "Name")
		self.assertEqual(columns[1].get("label"), "Module")
		self.assertTrue("User" in [d.get("name") for d in data])

	def test_save_or_delete_report_report(self):
		"""Test for validations when editing / deleting report_report of type ReportReport Builder"""

		try:
			report_report = frappe.get_doc(
				{
					"doctype": "ReportReport",
					"ref_doctype": "User",
					"report_report_name": "Test Delete ReportReport",
					"report_report_type": "ReportReport Builder",
					"is_standard": "No",
				}
			).insert()

			# Check for PermissionError
			create_user("test_report_report_owner@example.com", "Website Manager")
			frappe.set_user("test_report_report_owner@example.com")
			self.assertRaises(frappe.PermissionError, delete_report_report, report_report.name)

			# Check for ReportReport Type
			frappe.set_user("Administrator")
			report_report.db_set("report_report_type", "Custom ReportReport")
			self.assertRaisesRegex(
				frappe.ValidationError,
				"Only report_reports of type ReportReport Builder can be deleted",
				delete_report_report,
				report_report.name,
			)

			# Check if creating and deleting works with proper validations
			frappe.set_user("test@example.com")
			report_report_name = _save_report_report(
				"Dummy ReportReport",
				"User",
				json.dumps(
					[
						{
							"fieldname": "email",
							"fieldtype": "Data",
							"label": "Email",
							"insert_after_index": 0,
							"link_field": "name",
							"doctype": "User",
							"options": "Email",
							"width": 100,
							"id": "email",
							"name": "Email",
						}
					]
				),
			)

			doc = frappe.get_doc("ReportReport", report_report_name)
			delete_report_report(doc.name)

		finally:
			frappe.set_user("Administrator")
			frappe.db.rollback()

	def test_custom_report_report(self):
		reset_customization("User")
		custom_report_report_name = save_report_report(
			"Permitted Documents For User",
			"Permitted Documents For User Custom",
			json.dumps(
				[
					{
						"fieldname": "email",
						"fieldtype": "Data",
						"label": "Email",
						"insert_after_index": 0,
						"link_field": "name",
						"doctype": "User",
						"options": "Email",
						"width": 100,
						"id": "email",
						"name": "Email",
					}
				]
			),
		)
		custom_report_report = frappe.get_doc("ReportReport", custom_report_report_name)
		columns, result = custom_report_report.run_query_report_report(
			filters={"user": "Administrator", "doctype": "User"}, user=frappe.session.user
		)

		self.assertListEqual(["email"], [column.get("fieldname") for column in columns])
		admin_dict = frappe.core.utils.find(result, lambda d: d["name"] == "Administrator")
		self.assertDictEqual(
			{"name": "Administrator", "user_type": "System User", "email": "admin@example.com"}, admin_dict
		)

	def test_report_report_with_custom_column(self):
		reset_customization("User")
		response = run(
			"Permitted Documents For User",
			filters={"user": "Administrator", "doctype": "User"},
			custom_columns=[
				{
					"fieldname": "email",
					"fieldtype": "Data",
					"label": "Email",
					"insert_after_index": 0,
					"link_field": "name",
					"doctype": "User",
					"options": "Email",
					"width": 100,
					"id": "email",
					"name": "Email",
				}
			],
		)
		result = response.get("result")
		columns = response.get("columns")
		self.assertListEqual(
			["name", "email", "user_type"], [column.get("fieldname") for column in columns]
		)
		admin_dict = frappe.core.utils.find(result, lambda d: d["name"] == "Administrator")
		self.assertDictEqual(
			{"name": "Administrator", "user_type": "System User", "email": "admin@example.com"}, admin_dict
		)

	def test_report_report_permissions(self):
		frappe.set_user("test@example.com")
		frappe.db.delete("Has Role", {"parent": frappe.session.user, "role": "Test Has Role"})
		frappe.db.commit()
		if not frappe.db.exists("Role", "Test Has Role"):
			role = frappe.get_doc({"doctype": "Role", "role_name": "Test Has Role"}).insert(
				ignore_permissions=True
			)

		if not frappe.db.exists("ReportReport", "Test ReportReport"):
			report_report = frappe.get_doc(
				{
					"doctype": "ReportReport",
					"ref_doctype": "User",
					"report_report_name": "Test ReportReport",
					"report_report_type": "Query ReportReport",
					"is_standard": "No",
					"roles": [{"role": "Test Has Role"}],
				}
			).insert(ignore_permissions=True)
		else:
			report_report = frappe.get_doc("ReportReport", "Test ReportReport")

		self.assertNotEqual(report_report.is_permitted(), True)
		frappe.set_user("Administrator")

	def test_report_report_custom_permissions(self):
		frappe.set_user("test@example.com")
		frappe.db.delete("Custom Role", {"report_report": "Test Custom Role ReportReport"})
		frappe.db.commit()  # nosemgrep
		if not frappe.db.exists("ReportReport", "Test Custom Role ReportReport"):
			report_report = frappe.get_doc(
				{
					"doctype": "ReportReport",
					"ref_doctype": "User",
					"report_report_name": "Test Custom Role ReportReport",
					"report_report_type": "Query ReportReport",
					"is_standard": "No",
					"roles": [{"role": "_Test Role"}, {"role": "System Manager"}],
				}
			).insert(ignore_permissions=True)
		else:
			report_report = frappe.get_doc("ReportReport", "Test Custom Role ReportReport")

		self.assertEqual(report_report.is_permitted(), True)

		frappe.get_doc(
			{
				"doctype": "Custom Role",
				"report_report": "Test Custom Role ReportReport",
				"roles": [{"role": "_Test Role 2"}],
				"ref_doctype": "User",
			}
		).insert(ignore_permissions=True)

		self.assertNotEqual(report_report.is_permitted(), True)
		frappe.set_user("Administrator")

	# test for the `_format` method if report_report data doesn't have sort_by parameter
	def test_format_method(self):
		if frappe.db.exists("ReportReport", "User Activity ReportReport Without Sort"):
			frappe.delete_doc("ReportReport", "User Activity ReportReport Without Sort")
		with open(
			os.path.join(os.path.dirname(__file__), "user_activity_report_report_without_sort.json")
		) as f:
			frappe.get_doc(json.loads(f.read())).insert()

		report_report = frappe.get_doc("ReportReport", "User Activity ReportReport Without Sort")
		columns, data = report_report.get_data()

		self.assertEqual(columns[0].get("label"), "ID")
		self.assertEqual(columns[1].get("label"), "User Type")
		self.assertTrue("Administrator" in [d[0] for d in data])
		frappe.delete_doc("ReportReport", "User Activity ReportReport Without Sort")

	def test_non_standard_script_report_report(self):
		report_report_name = "Test Non Standard Script ReportReport"
		if not frappe.db.exists("ReportReport", report_report_name):
			report_report = frappe.get_doc(
				{
					"doctype": "ReportReport",
					"ref_doctype": "User",
					"report_report_name": report_report_name,
					"report_report_type": "Script ReportReport",
					"is_standard": "No",
				}
			).insert(ignore_permissions=True)
		else:
			report_report = frappe.get_doc("ReportReport", report_report_name)

		report_report.report_report_script = """
totals = {}
for user in frappe.get_all('User', fields = ['name', 'user_type', 'creation']):
	if not user.user_type in totals:
		totals[user.user_type] = 0
	totals[user.user_type] = totals[user.user_type] + 1

data = [
	[
		{'fieldname': 'type', 'label': 'Type'},
		{'fieldname': 'value', 'label': 'Value'}
	],
	[
		{"type":key, "value": value} for key, value in totals.items()
	]
]
"""
		report_report.save()
		data = report_report.get_data()

		# check columns
		self.assertEqual(data[0][0]["label"], "Type")

		# check values
		self.assertTrue("System User" in [d.get("type") for d in data[1]])

	def test_script_report_report_with_columns(self):
		report_report_name = "Test Script ReportReport With Columns"

		if frappe.db.exists("ReportReport", report_report_name):
			frappe.delete_doc("ReportReport", report_report_name)

		report_report = frappe.get_doc(
			{
				"doctype": "ReportReport",
				"ref_doctype": "User",
				"report_report_name": report_report_name,
				"report_report_type": "Script ReportReport",
				"is_standard": "No",
				"columns": [
					dict(fieldname="type", label="Type", fieldtype="Data"),
					dict(fieldname="value", label="Value", fieldtype="Int"),
				],
			}
		).insert(ignore_permissions=True)

		report_report.report_report_script = """
totals = {}
for user in frappe.get_all('User', fields = ['name', 'user_type', 'creation']):
	if not user.user_type in totals:
		totals[user.user_type] = 0
	totals[user.user_type] = totals[user.user_type] + 1

result = [
		{"type":key, "value": value} for key, value in totals.items()
	]
"""

		report_report.save()
		data = report_report.get_data()

		# check columns
		self.assertEqual(data[0][0]["label"], "Type")

		# check values
		self.assertTrue("System User" in [d.get("type") for d in data[1]])

	def test_toggle_disabled(self):
		"""Make sure that authorization is respected."""
		# Assuming that there will be report_reports in the system.
		report_reports = frappe.get_all(doctype="ReportReport", limit=1)
		report_report_name = report_reports[0]["name"]
		doc = frappe.get_doc("ReportReport", report_report_name)
		status = doc.disabled

		# User has write permission on report_reports and should pass through
		frappe.set_user("test@example.com")
		doc.toggle_disable(not status)
		doc.reload()
		self.assertNotEqual(status, doc.disabled)

		# User has no write permission on report_reports, permission error is expected.
		frappe.set_user("test1@example.com")
		doc = frappe.get_doc("ReportReport", report_report_name)
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.toggle_disable(1)

		# Set user back to administrator
		frappe.set_user("Administrator")

	def test_add_total_row_for_tree_report_reports(self):
		report_report_settings = {"tree": True, "parent_field": "parent_value"}

		columns = [
			{"fieldname": "parent_column", "label": "Parent Column", "fieldtype": "Data", "width": 10},
			{"fieldname": "column_1", "label": "Column 1", "fieldtype": "Float", "width": 10},
			{"fieldname": "column_2", "label": "Column 2", "fieldtype": "Float", "width": 10},
		]

		result = [
			{"parent_column": "Parent 1", "column_1": 200, "column_2": 150.50},
			{"parent_column": "Child 1", "column_1": 100, "column_2": 75.25, "parent_value": "Parent 1"},
			{"parent_column": "Child 2", "column_1": 100, "column_2": 75.25, "parent_value": "Parent 1"},
		]

		result = add_total_row(
			result,
			columns,
			meta=None,
			is_tree=report_report_settings["tree"],
			parent_field=report_report_settings["parent_field"],
		)
		self.assertEqual(result[-1][0], "Total")
		self.assertEqual(result[-1][1], 200)
		self.assertEqual(result[-1][2], 150.50)

	def test_cte_in_query_report_report(self):
		cte_query = textwrap.dedent(
			"""
			with enabled_users as (
				select name
				from `tabUser`
				where enabled = 1
			)
			select * from enabled_users;
		"""
		)

		report_report = frappe.get_doc(
			{
				"doctype": "ReportReport",
				"ref_doctype": "User",
				"report_report_name": "Enabled Users List",
				"report_report_type": "Query ReportReport",
				"is_standard": "No",
				"query": cte_query,
			}
		).insert()

		if frappe.db.db_type == "mariadb":
			col, rows = report_report.execute_query_report_report(filters={})
			self.assertEqual(col[0], "name")
			self.assertGreaterEqual(len(rows), 1)
		elif frappe.db.db_type == "postgres":
			self.assertRaises(frappe.PermissionError, report_report.execute_query_report_report, filters={})
