# Copyright (c) 2023, ratha and contributors
# For license information, please see license.txt

import ftplib, frappe
import os, shutil
import shlex, subprocess
from frappe.model.document import Document
from frappe.utils import cstr
import asyncio
from datetime import datetime
from frappe import conf
@frappe.whitelist()
def execute_backup_command():
    frappe.enqueue(run_backup_command,queue="long")
    return "Added To Queue"

@frappe.whitelist()
def run_backup_command():
    setting = frappe.get_doc('System Settings')
    site_name = cstr(frappe.local.site)
    folder = setting.ftp_backup_path
    if folder is None or folder == '' :
        folder = frappe.utils.get_site_path(conf.get("backup_path", "private/backups"))
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    asyncio.run(run_bench_command("bench --site " + site_name + " backup --with-files"))
    
    frappe.enqueue(upload_to_ftp,queue="long")

    return "Backup In Queue"

async def run_bench_command(command, kwargs=None):
    site = {"site": frappe.local.site}
    cmd_input = None
    if kwargs:
        cmd_input = kwargs.get("cmd_input", None)
        if cmd_input:
            if not isinstance(cmd_input, bytes):
                raise Exception(f"The input should be of type bytes, not {type(cmd_input).__name__}")
            del kwargs["cmd_input"]
        kwargs.update(site)
    else:
        kwargs = site
    command = " ".join(command.split()).format(**kwargs)
    command = shlex.split(command)
    subprocess.run(command, input=cmd_input, capture_output=True)

@frappe.whitelist()
def upload_to_ftp():
    folder_name = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    setting = frappe.get_doc('System Settings')
    site_name = cstr(frappe.local.site)
    backup_folder = setting.ftp_backup_path
    if backup_folder is None or backup_folder == '' :
        backup_folder = frappe.utils.get_site_path(conf.get("backup_path", "private/backups"))
    session = ftplib.FTP_TLS(setting.ftp_url,setting.ftp_user,setting.ftp_password)
    session.encoding = 'latin-1'
    if site_name in session.nlst():
        session.cwd(site_name)
        for folder in session.nlst():
            if folder != "." and folder != "..":
                created_date = folder.split('_', 1)[0]
                if(len(created_date) >= 10 ):
                    d1 = datetime.strptime(created_date, "%Y-%m-%d")
                    d2 = datetime.today()
                    if (d2-d1).days >= setting.delete_after:
                        session.cwd(folder)
                        for file in session.nlst():
                            if file != "." and file != "..":
                                session.delete(file)
                        session.cwd("../")
                        session.rmd(folder)
        session.mkd(folder_name)
        session.cwd(folder_name)
    else : 
        session.mkd(site_name)
        session.cwd(site_name)
        session.mkd(folder_name)
        session.cwd(folder_name)
    for filename in os.listdir(backup_folder):
        file_path = os.path.join(backup_folder, filename)
        file = open(file_path,'rb')
        session.storbinary('STOR ' + filename, file)
        file.close()
    session.quit()
    return "Backup Completed"


