#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib
from optparse import OptionParser
import sys
import os
import time
from lxml import etree
from genshi.template import NewTextTemplate
import traceback

'''
Created on 14/09/2009

@author: sebas
'''

class Scarab2Trac(object):
    '''
        Migra issues de scarab a tickets de Trac
    '''

    def __init__(self, conf):
        if not os.path.exists(conf):
            raise "El archivo %s no existe" % conf
        
        file = open(conf)

        try:
            xml = etree.XML(file.read())
        finally:
            file.close()
            
        self.options = {}
        
        common = xml.xpath ("/configuration/common")[0]

        self.options["xmlrpc-url"] = common.findtext("trac-xmlrpc-url")
        self.options["attachments-path"] = common.findtext("scarab-attachments-path")
        
        self.options["users-map"] = {}
        for u in xml.xpath ("/configuration/users-map/user"):
            self.options["users-map"][u.get("id-scarab")] = u.get("id-trac")
            
        self.options["global-attributes-map"] = {}
        for a in xml.xpath ("/configuration/global-attributes-map/attribute"):
            self.options["global-attributes-map"][a.get("id-scarab")] = Field(a.get("id-trac"), a.get("ignore") == "true", False, a.findtext("transformation")) 

        self.options["status-map"] = {}
        for a in xml.xpath ("/configuration/status-map/status"):
            self.options["status-map"][a.get("id-scarab")] = a.get("id-trac")
            
        scarab_artifacts = {}
        self.options["scarab-artifacts"] = scarab_artifacts
        self.options["ticket-types"] = {}
        
        for sa in xml.xpath ("/configuration/scarab-artifact"):
            type = sa.get("type")
            self.options["ticket-types"][type] = sa.get("ticket-type")
            scarab_artifacts[type] = {}

            scarab_artifacts[type]["attributes-map"] = {}
            for a in sa.xpath ("attributes-map/attribute"):
                scarab_artifacts[type]["attributes-map"][a.get("id-scarab")] = Field(a.get("id-trac"), a.get("ignore") == "true", False, a.findtext("transformation"))
            
            scarab_artifacts[type]["additional-attributes"] = {}
            for a in sa.xpath ("additional-attributes/attribute"):
                scarab_artifacts[type]["additional-attributes"][Field(a.get("id"), False, False, None)] = a.text 
        
        self.options["trac-statuses"] = self.get_server().ticket.status.getAll()
        self.options["trac-components"] = self.get_server().ticket.component.getAll()
        self.options["trac-milestones"] = self.get_server().ticket.milestone.getAll()
        self.options["trac-ticket-types"] = self.get_server().ticket.type.getAll()
        
        ticket_fields = {}
        for tf in self.get_server().ticket.getTicketFields():
            ticket_fields[tf["name"]] = tf

        self.options["trac-ticket-fields"] = ticket_fields 
        
    def issues_to_tickets(self, issues):
        warnings = {"components": [], "milestones": [] ,"fields": [], "volatiles": [], "users": [], "ticket-types": [], "new-tickets": 0, "existent-tickets": 0, "statuses": []}
        
        if not os.path.exists(issues):
            raise "El archivo '%s' no existe" % issues
        
        file = open(issues)

        try:
            xml = etree.XML(file.read())
        finally:
            file.close()

        tickets = []
        me = xml.xpath("/scarab-issues/module")[0]
        
        module = {}
        module["id"] = me.findtext("id")
        module["name"] = me.findtext("name")

        for issue in xml.xpath("/scarab-issues/issues/issue"):
            genshi_context = {}
            ticket = {}
            tickets.append(ticket)

            creation = issue.xpath("activity-sets/activity-set/type[. = 'Create Issue']/..")[0]
            updates = issue.xpath("activity-sets/activity-set/type[. = 'Edit Issue']/..")

            ticket["id"] = issue.findtext("id")
            ticket["type"] = issue.findtext("artifact-type")
            ticket["owner"] = creation.findtext("created-by")
            ticket["created"] = creation.xpath("created-date/timestamp/text()")[0]
            
            genshi_context["id"] = ticket["id"]
            genshi_context["type"] = ticket["type"]
            genshi_context["owner"] = ticket["owner"]
            genshi_context["created"] = ticket["created"]
            
            ticket["creation-activities"] = self.get_activities(ticket["type"], creation, genshi_context)
            
            ticket["updates"] = []
            for u in updates:
                ticket["updates"].append(self.get_activities(ticket["type"], u, genshi_context))

            attrs = self.options["scarab-artifacts"][ticket["type"]]["additional-attributes"]
            for f in attrs:
                ticket["creation-activities"].append(Activity(f, self.transform(attrs[f], genshi_context), None, "Atributo seteado automaticamente en la migracion"))

            # validaciones
            for a in ticket["creation-activities"]:
                summary = self.validate_fields(a, genshi_context, warnings)
                if summary != "": 
                    if len(self.get_id_ticket(summary)) > 0:
                        warnings["existent-tickets"] += 1
                    else: 
                        warnings["new-tickets"] += 1
                
            for u in ticket["updates"]:
                for a in u:
                    self.validate_fields(a, genshi_context, warnings)

            type = ticket["type"]
            if type in self.options["ticket-types"]:
                type = self.options["ticket-types"][type]
            
            if type not in self.options["trac-ticket-types"]:
                warnings["ticket-types"].append(type)
            ticket["type"] = type

        warnings["volatiles"] = unique(warnings["volatiles"]) 
        warnings["users"] = unique(warnings["users"])
        warnings["ticket-types"] = unique(warnings["ticket-types"])
        warnings["statuses"] = unique(warnings["statuses"])
        warnings["milestones"] = unique(warnings["milestones"])
        warnings["fields"] = unique(warnings["fields"])
        warnings["components"] = unique(warnings["components"])
        warnings["statuses"] = unique(warnings["statuses"])
        
        return (module, tickets, warnings)

    def validate_fields(self, activity, ctx, warnings):
        if activity.field.transformation != None:
            activity.value = self.transform(activity.field.transformation, ctx)
                    
        summary = ""
        if activity.field.volatil:
            warnings["volatiles"].append(activity.field.id)
        elif activity.value and activity.field.id in ["cc", "owner"] and not self.get_user(activity.value):
            warnings["users"].append(activity.value)
        elif activity.field.id == "summary":
            summary = activity.value
        elif activity.field.id == "status":
            id_status = activity.value if activity.value not in self.options["status-map"] else self.options["status-map"][activity.value]
            if id_status not in self.options["trac-statuses"]:
                warnings["statuses"].append(id_status)
            activity.value = id_status
        elif activity.field.id == "milestone" and activity.value not in self.options["trac-milestones"]:
            warnings["milestones"].append(activity.value)
        elif activity.field.id == "component" and activity.value not in self.options["trac-components"]:
            warnings["components"].append(activity.value)
        elif activity.field.id != "Null attribute" and not activity.field.ignore and activity.field.id not in self.options["trac-ticket-fields"]:
            warnings["fields"].append(activity.field.id)
        
        return summary
    
    def transform(self, template, ctx):
        return NewTextTemplate(template).generate(ticket=ctx).render()
          
    def get_activities(self, scarab_artifact, activityset, values):
        activities = []

        for a in activityset.xpath("activities/activity"):
            attach = a.find("attachment")

            field = self.get_field(scarab_artifact, a.findtext("attribute"))
            value = a.findtext("new-value")
            description = a.findtext("description")

            activities.append(Activity(field, value, attach, description))

            values[field.id] = value

        return activities

    def get_field(self, scarab_artifact, id):
        if id in self.options["global-attributes-map"]:
            return self.options["global-attributes-map"][id]
        
        artifact = self.options["scarab-artifacts"][scarab_artifact]
        if id in artifact["attributes-map"]:
            return artifact["attributes-map"][id]

        return Field(id, False, True)
    
    def get_user(self, id):
        if id in self.options["users-map"]:
            return self.options["users-map"][id]
        return None

    def get_id_ticket(self, id):
        try:
            transf = id.replace("=", "%3D")
            return self.get_server().ticket.query('summary=%s' % transf)
        except:
            raise "Error al buscar '%s'"%transf

    def get_server(self):
        return xmlrpclib.ServerProxy(self.options["xmlrpc-url"])

    def update_tickets(self, module, tickets):
        server = self.get_server()

        for t in tickets:
            attrs = {"type": t["type"], "owner": t["owner"]}
            summary = ""
            
            attachs_in_create = []
            
            for a in t["creation-activities"]:
                if a.attach is not None:
                    name = a.attach.findtext("filename")
                    description = a.attach.findtext("name")
                    
                    if name != None:
                        base_path = "%s/mod%s" % (self.options["attachments-path"], module["id"])
                        file_name = "%s_%s_%s" % (t["id"], a.attach.findtext("id"), name)
                        
                        file = None
                        for d in os.listdir(base_path):
                            candidate = os.path.join(base_path, d, file_name)
                            if os.path.exists(candidate):
                                file = open(candidate)
                                break
                        if not file:
                            print "No se encontró el archivo '%s'" % file_name

                        attach_in_create = {}
                        attach_in_create["content"] = xmlrpclib.Binary(file.read())
                        attach_in_create["name"] = name
                        attach_in_create["description"] = description
                        
                        attachs_in_create.append(attach_in_create)

                elif a.value:
                    if a.field.id == "summary":
                        summary = a.value
                    
                    attrs[a.field.id] = a.value

            if len(self.get_id_ticket(summary)) > 0:
                print "El ticket '%s' existe, actualización aún no implementada" % t["id"]
                continue

            id = server.ticket.create(summary, "Ticket Scarab %s" % t["id"], attrs, True)
            print "Se creó %s" % t["id"],
            delay()
            
            for attach_in_create in attachs_in_create: 
                server.ticket.putAttachment(id, attach_in_create["name"], attach_in_create["description"], attach_in_create["content"])

            print "- actualizando ",
            for u in t["updates"]:
                attrs = {}
                descriptions = []
                cc = []
                for a in u:
                    if a.attach is not None:
                        name = a.attach.findtext("filename")
                        description = a.attach.findtext("name")
                        
                        if name != None:
                            base_path = "%s/mod%s" % (self.options["attachments-path"], module["id"])
                            file_name = "%s_%s_%s" % (t["id"], a.attach.findtext("id"), name)
                            
                            file = None
                            for d in os.listdir(base_path):
                                candidate = os.path.join(base_path, d, file_name)
                                if os.path.exists(candidate):
                                    file = open(candidate)
                                    break
                            if not file:
                                print "No se encontró el archivo '%s'" % file_name
                            
                            content = xmlrpclib.Binary(file.read())
                            server.ticket.putAttachment(id, name, description, content)
                            delay()
                    elif a.value:
                        if a.field.id == 'cc':
                            cc.append(self.get_user(a.value))
                        elif a.field.id == 'owner':
                            attrs[a.field.id] = self.get_user(a.value)
                        elif not a.field.ignore and a.field.id not in ['summary', 'Null attribute']:
                            attrs[a.field.id] = a.value

                        descriptions.append(a.description)

                if len(cc) > 0:
                    attrs['cc'] = ", ".join(cc);
                
                try:
                    server.ticket.update(id, "\n".join(descriptions), attrs)
                except :
                    traceback.print_exc(file=sys.stdout)
                    print
                    
                delay()

                print ".",
            print

class Field(object):
    def __init__(self, id, ignore=True, volatil=False, transformation = None):
        self.id = id
        self.ignore = ignore
        self.volatil = False if id == "Null attribute" else volatil
        self.transformation = transformation

    def __repr__(self):
        return "Field (id = '%s', ignore = '%s', volatil = '%s')" % (self.id, self.ignore, self.volatil)

class Activity(object):
    def __init__(self, field, value, attach, description):
        self.field = field
        self.value = value
        self.attach = attach
        self.description = description


    def __repr__(self):
        return "Activity(field = '%s', value = '%s', attach = '%s', description = '%s')" % (self.field.id, self.value, self.attach, self.description)

def unique(list):
    m = {}
    for obj in list:
        m[obj] = 1
    return m.keys()

'''
   Es necesario hacer un delay entre cada invocacion XML-RPC debido a un bug reportado 
'''
def delay():
    time.sleep(1.0)

if __name__ == '__main__':
    opts = OptionParser()
    opts.add_option("--conf", "-c", help="Archivo de configuracion", default=None, dest="conf")
    opts.add_option("--scarab-issues", "-s", help="Archivo con los issues exportados desde Scarab", default=None, dest="scarab")
    options = opts.parse_args()[0]

    if not options.conf:
        print "Debe especificar un archivo de configuración"
        sys.exit(1);
        
    if not options.scarab:
        print "Debe especificar el archivo con los issues de scarab"
        sys.exit(1);

    if not os.path.exists(options.conf):
        print "El archivo de configuracion '%s' no existe"%options.conf
        sys.exit(1)
        
    if not os.path.exists(options.scarab):
        print "El archivo con los issues scarab: '%s' no existe"%options.scarab
        sys.exit(1)

    s2t = Scarab2Trac(options.conf)
    module, tickets, warnings = s2t.issues_to_tickets(options.scarab)
    
    print "Informe de issues:"
    for w in warnings:
        print "\t%s = %s"%(w, warnings[w])

    print "¿Desea continuar (s/n)?",
    cont = sys.stdin.readline().replace("\n", "").upper()
    if cont in ["", "S"]:
        s2t.update_tickets(module, tickets)
