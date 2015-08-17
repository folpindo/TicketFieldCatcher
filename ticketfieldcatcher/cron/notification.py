#!/bin/env python

"""
Add this on your trac configuration:

[field_catcher]
host = localhost
user = tracuser
pwd = tracuserpassword
db = tracdatabase
"""

import os
import sys
import MySQLdb
import smtplib
import ConfigParser as parser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logbook import FileHandler, Logger
from time import sleep

class TicketFieldCatcher_Notifier:

    def __init__(self,config_file=None):
        if os.path.isfile(config_file):
            self.config_file = config_file
        else:
            print "The config file %s does not exist." % config_file
            sys.exit(1)

        self.config = parser.ConfigParser()
        self.config.read(self.config_file)
        
        host = None
        user = None
        pwd = None
        db = None
        cb = "field_catcher"

        config = self.config
        
        if config is not None:
            if config.has_section(cb):
                if config.has_option(cb,"user"):
                    user = config.get(cb,"user")
                if config.has_option(cb,"pwd"):
                    pwd = config.get(cb,"pwd")
                if config.has_option(cb,"db"):
                    db = config.get(cb,"db")
                if config.has_option(cb,"host"):
                    host = config.get(cb,"host")

        log_label = None
        logger_name = "[Ticket Field Catcher]"

	if config.has_option(cb,"logger_name"):
            logger_name = config.get(cb,"logger_name")
            
	self.logger = Logger(logger_name)

        logger_log_file = "/var/log/field-catcher.log"

        if config.has_option(cb,"logger_log_file"):
            logger_log_file = config.get(cb,"logger_log_file")
            
        log_handler = FileHandler(logger_log_file)
        log_handler.push_application()

        self.db = MySQLdb.connect(host,user,pwd,db)

    def close_connections(self):
        if self.db:
            self.db.close()
            
    def send_notification(self):
        db = self.db
        cursor = db.cursor()
        config = self.config
 	days_overdue = 365
        cb = "field_catcher"

        if config.has_section(cb):
            if config.has_option(cb,"threshold_days"):
                days_overdue = config.get(cb,"threshold_days")
                
        overdue_sku = """
SELECT
    t.id,
    dfc.brand,
    dfc.sku,
    t.status,
    (
         CASE
             WHEN DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) = ''
                  THEN "0"
             ELSE
                  DATEDIFF(NOW(),DATE(FROM_UNIXTIME(time/1000000)))
         END

    ) as "overdue",
    FROM_UNIXTIME(t.changetime/1000000) as 'changetime',
    t.milestone,
    t.reporter,
    t.owner,
    t.summary

FROM
    ticket as t

LEFT JOIN
    daco_field_catcher as dfc on t.id = dfc.ticket

WHERE
    DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) < %s
    and t.status <> 'closed' and dfc.sku <> ''
       """
        
        cursor.execute(overdue_sku,days_overdue)
        data_sku = cursor.fetchall()
        csv = "ticket,brand,sku,status,days overdue,modified date,milestone,reporter,owner,summary\n"
        
        for cont in data_sku:
            row = []
            for v in cont:
                if v is None:
                    v = ''
                row.append(v)
            csv = csv + "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])

        config = self.config
        file_attachment = "overdue-tickets.csv"
        cb = "field_catcher"

        if config.has_option(cb,"file_attachment_name"):
            file_attachment = config.get(cb,"file_attachment_name")

        attachment = MIMEText(csv)
        attachment.add_header('Content-Disposition','attachment',filename=file_attachment)

        sender = "user.local"
        
        if config.has_option(cb,"mail_sender"):
            sender = config.get(cb,"mail_sender")

        recipients = "folpindo@gmail.com"

        if config.has_option(cb,"mail_recipients"):
            recipients = config.get(cb,"mail_recipients")

        message = "Attached is the list of tickets that are found to be open for a pre-defined number of days."
        if config.has_option(cb,"mail_message"):
            message = config.get(cb,"mail_message")
        
        msg = MIMEMultipart("alternative")

        subject = "Trac Field Catcher -- default subject"

        if config.has_option(cb,"mail_subject"):
            subject = config.get(cb,"mail_subject")
        
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipients
        body = message
        content = MIMEText(body,'plain')
        msg.attach(attachment)

        smtp_host = "localhost"
        if config.has_option(cb,"smtp_host"):
            smtp_host = config.get(cb,"smtp_host")
        
        s = smtplib.SMTP(smtp_host)
        s.sendmail(sender,[recipients],msg.as_string())
        s.quit()

if __name__ == '__main__':
    notifier = TicketFieldCatcher_Notifier('/var/www/trac/conf/trac.ini')
    notifier.send_notification()
    
