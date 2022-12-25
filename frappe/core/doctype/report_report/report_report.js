frappe.ui.form.on("Report Report", {
	refresh: function (frm) {
		if (frm.doc.is_standard === "Yes" && !frappe.boot.developer_mode) {
			// make the document read-only
			frm.disable_form();
		} else {
			frm.enable_save();
		}

		let doc = frm.doc;
		if (!doc.__islocal) {
			frm.add_custom_button(
				__("Show Report Report"),
				function () {
					switch (doc.report_type) {
						case "Report Report Builder":
							frappe.set_route("List", doc.ref_doctype, "Report Report", doc.name);
							break;
						case "Query Report Report":
							frappe.set_route("query-report", doc.name);
							break;
						case "Script Report Report":
							frappe.set_route("query-report", doc.name);
							break;
						case "Custom Report Report":
							frappe.set_route("query-report", doc.name);
							break;
					}
				},
				"fa fa-table"
			);
		}

		if (doc.is_standard === "Yes" && frm.perm[0].write) {
			frm.add_custom_button(
				doc.disabled ? __("Enable Report Report") : __("Disable Report Report"),
				function () {
					frm.call("toggle_disable", {
						disable: doc.disabled ? 0 : 1,
					}).then(() => {
						frm.reload_doc();
					});
				},
				doc.disabled ? "fa fa-check" : "fa fa-off"
			);
		}
	},

	ref_doctype: function (frm) {
		if (frm.doc.ref_doctype) {
			frm.trigger("set_doctype_roles");
		}
	},

	set_doctype_roles: function (frm) {
		return frm.call("set_doctype_roles").then(() => {
			frm.refresh_field("roles");
		});
	},
});
