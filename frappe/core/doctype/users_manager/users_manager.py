# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UsersManager(Document):
	def on_update(self):
		users = frappe.db.sql("select username from `tabUser` where username='{}'".format(self.username))
		if users:
			update_user(self)
		else:
			add_new_user(self)
   
  
def add_new_user(self):

	sql = """
				insert into `tabUser` (
					name,
					enabled,
					username,
					email,
					first_name,
					full_name,
					language,
					time_zone,
					user_type,
					desk_theme,
					creation,
					modified,
					modified_by,
					owner
   			)values(
				'{0}',
				{1},
				'{2}',
				'{3}',
				'{4}',
				'{4}',
				'{5}',
				'Asia/Phnom_Penh',
				'System User',
				'Light',
				'{6}',
				'{7}',
				'{8}',
				'{8}'
			)
	""".format(
		self.email,
		self.enabled,
		self.name,
		self.email,
		self.full_name,
		self.language,
		self.creation,
		self.modified,
		self.owner
	)
	
	frappe.db.sql(sql)
 
	#update role
 
	#update module 

 
def update_user(self):
    sql = "update `tabUser` set "
    frappe.msgprint("update user")
