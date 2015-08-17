#!/bin/env python


"""

This will  be used to populate a table which contains the basic fields:

1. ticket id
2. ticket date created - time
3. ticket date closed or modified - changetime
4. status
5. brand
6. sku 
7. milestone
8. reporter
9. owner

Notes:

The ticket_custom table comprises of the following fields:
1. ticket
2. name
3. values

SELECT
    t.id,
    tc.value as 'sku',
    t.status,
    (
         CASE
             WHEN DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) = ''
                  THEN "0"
             ELSE
                  DATEDIFF(NOW(),DATE(FROM_UNIXTIME(time/1000000)))
         END

    ) as "days",
    FROM_UNIXTIME(t.changetime/1000000) as 'changetime',
    t.milestone,
    t.reporter,
    t.owner,
    t.summary

FROM
    ticket as t

LEFT JOIN
    ticket_custom as tc on t.id = tc.ticket

WHERE
    DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) < 10000
    and t.status <> 'closed'
    and tc.name = 'sku'
    and tc.value <> ''
LIMIT 1\G

SELECT
    t.id,
    tc.value as 'brand',
    t.status,
    (
         CASE
             WHEN DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) = ''
                  THEN "0"
             ELSE
                  DATEDIFF(NOW(),DATE(FROM_UNIXTIME(time/1000000)))
         END

    ) as "days",
    FROM_UNIXTIME(t.changetime/1000000) as 'changetime',
    t.milestone,
    t.reporter,
    t.owner,
    t.summary

FROM
    ticket as t

LEFT JOIN
    ticket_custom as tc on t.id = tc.ticket

WHERE
    DATEDIFF(NOW(),DATE(FROM_UNIXTIME(t.time/1000000))) < 10000
    and t.status <> 'closed'
    and tc.name = 'brand'
    and tc.value <> ''
LIMIT 1\G

"""

import re
from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.web import IRequestHandler

from json import dumps, loads
#from urllib import urlencode, unquote
#from urlparse import urlparse, parse_qsl, ParseResult
#import urllib.request

try:
    from urllib.parse import urlparse,parse_qs
except ImportError:
    from urlparse import urlparse,parse_qs
    
class TicketFieldCatcher(Component):

    implements(ITicketChangeListener,IRequestHandler)
    def match_request(self,req):
        return re.match(r'/get_sku(?:_trac)?(?:/.*)?$',req.path_info)
    def get_tickets(self,sku):
        config = self.config
        env = self.env
        tickets = []
        with env.db_query as db:
            cursor = db.cursor()
            cursor.execute("SELECT ticket FROM field_catcher WHERE sku='%s'" % sku)
            rows = cursor.fetchall()
            for t in rows:
                tickets.append(t[0])
            return tickets
    
    def process_request(self,req):
        method = req.method
        path_info = type(req.path_info)
        query = req.query_string
        remote_addr = req.remote_addr
        remote_user = req.remote_user
        scheme = req.scheme
        server_name = req.server_name
        server_port = req.server_port
        o = urlparse(query)
        dict_parsed = parse_qs(query)
        tickets = self.get_tickets(dict_parsed["sku"][0])
        content = """
        {
            "sku":"%s",
            "tickets":%s
        }
"""% (dict_parsed["sku"][0],dumps(tickets))
        req.send_response(200)
        req.send_header('Content-Type','application/json')
        req.send_header('Content-Length',len(content))
        req.end_headers()
        req.write(content)
    
    def ticket_created(self,ticket):
        ticket_id = ticket.id
        config = self.config
        env = self.env
        sku = None
        brand = None
        sku = ticket.get_value_or_default("sku")
        brand = ticket.get_value_or_default("brand")
        data = (ticket_id,sku,brand)
        self.log.debug("length#brand: %s, length#sku: %s" % (len(brand),len(sku)))
        
        if brand or sku:
            with env.db_query as db:
                cursor = db.cursor()           
                cursor.execute("INSERT INTO field_catcher(ticket,sku,brand) values('%s','%s','%s')" % data)
            self.log.debug("ticket_created: %s" % ticket.id)

    def ticket_changed(self,ticket,comment,author,old_values):
        ticket_id = ticket.id
        config = self.config
        env = self.env
        sku = ticket.get_value_or_default("sku")
        brand = ticket.get_value_or_default("brand")
        row = None
        with env.db_query as db:
            cursor = db.cursor()
            if(cursor.execute("SELECT * FROM field_catcher WHERE ticket=%s" % ticket_id)):
                for tid,s,b,d in cursor:
                    row = {'ticket':tid,'sku':s,'brand':b,'deleted':d}
                    if row['sku'] != sku or row['brand'] != brand:
                        cursor.execute("UPDATE field_catcher SET sku='%s',brand='%s' WHERE ticket=%s" % (sku,brand,ticket_id))
            else:
                self.ticket_created(ticket)
      
    def ticket_deleted(self,ticket):
        ticket_id = ticket.id
        config = self.config
        env = self.env
        with env.db_query as db:
            cursor = db.cursor()
            if(cursor.execute("DELETE FROM field_catcher WHERE ticket=%s" % ticket_id)):
                self.log.debug("Deleted ticket %s on field_catcher table" % ticket.id)
            else:
                self.log.debug("Unable to delete ticket %s from field_catcher table" % ticket.id)

    def ticket_comment_modified(self,ticket,cdate,author,comment,old_comment):
        pass
        #self.log.debug("ticket_comment_modified: %s" % ticket.id)
    def ticket_change_deleted(self,ticket,cdate,changes):
        pass
        #self.log.debug("ticket_change_deleted: %s" % ticket.id)
