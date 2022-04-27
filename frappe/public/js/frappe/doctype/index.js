frappe.provide("frappe.model");

/*
	Common class for handling client side interactions that
	apply to both DocType form and customize form.
*/
frappe.model.DocTypeController = class DocTypeController extends frappe.ui.form.Controller {
	max_attachments() {
		if (!this.frm.doc.max_attachments) {
			return;
		}
		const is_attach_field = (f) => ["Attach", "Attach Image"].includes(f.fieldtype);
		const no_of_attach_fields = this.frm.doc.fields.filter(is_attach_field).length;

		if (no_of_attach_fields > this.frm.doc.max_attachments) {
			this.frm.set_value("max_attachments", no_of_attach_fields);
			const label = this.frm.get_docfield("max_attachments").label;
			frappe.show_alert(
				__("Number of attachment fields are more than {}, limit updated to {}.", [label, no_of_attach_fields]));
		}
	}

	naming_rule() {
		// set the "autoname" property based on naming_rule
		if (this.frm.doc.naming_rule && !this.frm.__from_autoname) {

			// flag to avoid recursion
			this.frm.__from_naming_rule = true;

			switch (this.frm.doc.naming_rule) {
				case "Set by user":
					this.frm.set_value("autoname", "Prompt");
					break;
				case "Autoincrement":
					this.frm.set_value("autoname", "autoincrement");
					break;
				case "By fieldname":
					this.frm.set_value("autoname", "field:");
					break;
				case 'By "Naming Series" field':
					this.frm.set_value("autoname", "naming_series:");
					break;
				case "Expression":
					this.frm.set_value("autoname", "format:");
					break;
				case "Expression (old style)":
					break;
				case "Random":
					this.frm.set_value("autoname", "hash");
					break;
			}
			setTimeout(() => (this.frm.__from_naming_rule = false), 500);

			this.set_naming_rule_description();
		}

	}

	set_naming_rule_description() {
		let naming_rule_description = {
			'Set by user': '',
			'Autoincrement': 'Uses Auto Increment feature of database.<br><b>WARNING: After using this option, any other naming option will not be accessible.</b>',
			'By fieldname': 'Format: <code>field:[fieldname]</code>. Valid fieldname must exist',
			'By "Naming Series" field': 'Format: <code>naming_series:[fieldname]</code>. Default fieldname is <code>naming_series</code>',
			'Expression': 'Format: <code>format:EXAMPLE-{MM}morewords{fieldname1}-{fieldname2}-{#####}</code> - Replace all braced words (fieldnames, date words (DD, MM, YY), series) with their value. Outside braces, any characters can be used.',
			'Expression (old style)': 'Format: <code>EXAMPLE-.#####</code> Series by prefix (separated by a dot)',
			'Random': '',
			'By script': ''
		};

		if (this.frm.doc.naming_rule) {
			this.frm.get_field('autoname').set_description(naming_rule_description[this.frm.doc.naming_rule]);
		}
	}

	autoname() {
		// set naming_rule based on autoname (for old doctypes where its not been set)
		if (this.frm.doc.autoname && !this.frm.doc.naming_rule && !this.frm.__from_naming_rule) {
			// flag to avoid recursion
			this.frm.__from_autoname = true;
			const autoname = this.frm.doc.autoname.toLowerCase();

			switch (autoname) {
				case 'prompt':
					this.frm.set_value('naming_rule', 'Set by user');
					break;
				case 'autoincrement':
					this.frm.set_value('naming_rule', 'Autoincrement');
					break;
				case (autoname.startsWith('field:')):
					this.frm.set_value('naming_rule', 'By fieldname');
					break;
				case (autoname.startsWith('naming_series:')):
					this.frm.set_value('naming_rule', 'By "Naming Series" field');
					break;
				case (autoname.startsWith('format:')):
					this.frm.set_value('naming_rule', 'Expression');
					break;
				case 'hash':
					this.frm.set_value('naming_rule', 'Random');
					break;
				default:
					this.frm.set_value('naming_rule', 'Expression (old style)');
			}
			setTimeout(() => (this.frm.__from_autoname = false), 500);
		}

		this.frm.set_df_property('fields', 'reqd', this.frm.doc.autoname !== 'Prompt');
	}
};
