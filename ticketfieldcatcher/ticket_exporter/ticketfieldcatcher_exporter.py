#!/bin/env python

import MySQLdb
from logbook import FileHandler, Logger
from time import sleep

class TicketFieldCatcher_Exporter:

    def __init__(self):
	self.logger = Logger('[Ticket Field Catcher Exporter]')
        log_handler = FileHandler('/var/log/field-catcher-exporter.log')
        log_handler.push_application()
        self.db = MySQLdb.connect("localhost","tracuser","tracuserpassword","trac")

    def close_connections(self):
        if self.db:
            self.db.close()
            
    def export_tickets(self):
        db = self.db
        source_cursor = db.cursor()
        target_cursor = db.cursor()
        source_query_sku = """
            SELECT
                t.id,
                tc.value as 'sku'
            FROM
                ticket as t
            LEFT JOIN
                ticket_custom as tc on t.id = tc.ticket
            WHERE
                tc.name = 'sku' and tc.value <> ''
        """
        source_cursor.execute(source_query_sku)
        data_sku = source_cursor.fetchall()
        for row in data_sku:
             target_query="INSERT INTO field_catcher(ticket,sku) VALUES(%s,%s)"
             target_cursor.execute(target_query,(row[0],row[1]))
             self.logger.info("ticket:%s,\tsku:%s" % (row[0],row[1]))
             if len(row[1]) < 3:
                 sleep(1)

    def update_tickets(self):
        db = self.db
        source_cursor = db.cursor()
        checker_cursor = db.cursor()
        updater_cursor = db.cursor()
        source_query_brand = """
            SELECT
                t.id,
                tc.value as 'brand'
            FROM
                ticket as t
            LEFT JOIN
                ticket_custom as tc on t.id = tc.ticket
            WHERE
                tc.name = 'brand' and tc.value <> ''
                
        """
        source_cursor.execute(source_query_brand)
        data_brand = source_cursor.fetchall()
        for row in data_brand:
            if checker_cursor.execute("SELECT * FROM field_catcher WHERE ticket=%s",(row[0])):
                updater_cursor.execute("UPDATE field_catcher SET brand=%s WHERE ticket=%s", (row[1],row[0]))
            else:
                updater_cursor.execute("INSERT INTO field_catcher(ticket,brand) VALUES(%s,%s)", (row[0],row[1]))
            self.logger.info("ticket:%s,\tbrand:%s" % (row[0],row[1]))
            if len(row[1]) < 3:
                sleep(1)

if __name__ == '__main__':
    exporter = TicketFieldCatcher_Exporter()
    exporter.export_tickets()
    exporter.update_tickets()
    exporter.close_connections()
