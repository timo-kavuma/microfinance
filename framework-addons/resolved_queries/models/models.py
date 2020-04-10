# -*- coding: utf-8 -*-

import os
import os.path as path
import re
import subprocess
import base64

from odoo import models, fields, api,tools,_
from odoo.exceptions import UserError

class resolvedQueries(models.Model):
    _name = 'resolved.queries'
    _rec_name='model_id'

    prefixs=[
            ('SELECT','SELECT'),
            ('FROM','FROM'),
            ('DELECT','DELETE'),
            ('UPDATE','UPDATE')
            ]

    @api.onchange('model_id', 'prefix')
    def _onchange_example_query(self):
        if self.model_id and self.prefix:
            irModel=self.env['ir.model']
            model=self.env[self.model_id.model]
            table=model._table
            self.table=table
            self.search_parameter=r'%s\s\"%s\"' % (self.prefix,table)
            self.total_row=model.search_count([])

    def _compute_get_log_level(self):
        for record in self:
            record.log_level=tools.config.get('log_level')

    #~ Modelo que quiere hacer la prueba consultas resueltas
    model_id = fields.Many2one(
                            'ir.model',
                            string='Model name',
                            required=True,
                            help="""Model who wants to do the test resolved queries""")
    name = fields.Char(
                        string='Technical name',
                        related='model_id.model',
                        readonly=True)
    table = fields.Char(
                        string='Model Table',
                        readonly=True)
    #~ parametro de configuracion del nivel del Log
    log_level = fields.Char(
                        string='Log level',
                        readonly=True,
                        compute='_compute_get_log_level',
                        help="""Log level configuration parameter,
                        To test the modules of go ui view cache, web base cache or website
                        base cache, you must change the log_leve parameter in the configuration
                        file to debug_sql""")
    #~ prefijo de busqueda que se va a utilizar en el grep en el  achivo del log
    prefix= fields.Selection(
                            prefixs,
                            string='Query Prefix',
                            required=True,
                            help="""search prefix to be used in the grep in the log file""")
    #~ Expresión regular de busqueda, usted puede cambiar la expresión regular, debe conocer de expresion regular de python.
    search_parameter=fields.Text(
                            string='Regular Expression',
                            required=True,
                            help="""Regular search expression, you can change the regular
                            expression, you must know about regular python expression.""")
    #~ Total de query que coinciden con la expresión regular.
    total= fields.Integer(
                        string='Total Queries',
                        readonly=True,
                        help="""Total query matching the regular expression""")
    #~ Toltal de registros del modelo
    total_row= fields.Integer(
                            string='Total Records',
                            readonly=True,
                            help="""Total model records""")
     #~ Desactivar o activar de la ejecución del  grep en el log
    active=fields.Boolean(
                        string='Active',
                        default=True,
                        help="""Deactivate or activate grep execution in the log""")
    #~ Descargue el archivo con el resultado
    query_file=fields.Binary(
                        string='File Query',
                        attachment=True,
                        help="""Download the file with the result""")
    store_fname = fields.Char(string="File Name")

    def clear_log(self):
        logfile=tools.config.get('logfile')
        with open(logfile, "w"):
            pass
        return

    @api.multi
    def run_resolved_queries(self):
        irModel=self.env['ir.model']
        logfile=tools.config.get('logfile')
        msg=_('You must configure the absolute path of the ')
        msg=msg+_('logfile in the configuration file.')
        if not logfile:
            raise UserError(_(msg))
        if not path.isfile(logfile):
            raise UserError(_(msg))
        if not os.access(logfile, os.R_OK):
            msg=_('The %s file does not have read permission.' % logfile)
            raise UserError(_(msg))
        if self.search_parameter:
            model=self.env[self.model_id.model]
            self.total_row=model.search_count([])
            to_date=fields.Date.today()
            patron=re.compile(self.search_parameter)
            linesFound=''
            total=0
            cant=0
            with open(logfile, "r") as f:
                lines = f.readlines()
                for line in lines:
                    total+=1
                    match = patron.search(line)
                    if match:
                        cant+=1
                        linesFound+='N-%s:L-%s:%s' %(str(cant),str(total),line)
            if linesFound:
                self.query_file = base64.b64encode(bytes(linesFound, 'utf-8'))
                self.store_fname="%s_%s_t_%s.txt" %(self.model_id.name,to_date,str(cant))
            else:
                self.query_file = ''
                self.store_fname=''
            self.total=cant

class ResolvedQueriesWizard(models.TransientModel):
    """ Run resolved queries wizard. """
    _name = 'resolved.queries.wizard'
    _description = 'Run resolved queries wizard'

    def _default_resolved_queries_ids(self):
        resolved_queries_ids = self._context.get('active_model') == 'resolved.queries' and self._context.get('active_ids') or []
        return resolved_queries_ids

    resolved_queries_ids=fields.Many2many(
                                        'resolved.queries',
                                        string='Resolved Queries',
                                        default=_default_resolved_queries_ids)
    #~ Total de coincidencias con el parametro de busqueda que se utiliza en el grep -rn 'search parameter'  | wc -l.
    total= fields.Integer(
                        string='Total Queries',
                        readonly=True,
                        help="""Total matches with the search parameter used in the grep -rn 'search parameter' | wc -l.""")
    #~ Descargue el archivo con el resultado del grep
    query_file=fields.Binary(
                        string='File Query',
                        attachment=True,
                        help="""Download the file with the grep result""")
    store_fname = fields.Char(string="File Name",readonly=True)

    def clear_log(self):
        logfile=tools.config.get('logfile')
        with open(logfile, "w"):
            pass
        return

    @api.multi
    def run_resolved_queries(self):
        irModel=self.env['ir.model']
        logfile=tools.config.get('logfile')
        msg=_('You must configure the absolute path of the ')
        msg=msg+_('logfile in the configuration file.')
        if not logfile:
            raise UserError(_(msg))
        if not path.isfile(logfile):
            raise UserError(_(msg))
        if not os.access(logfile, os.R_OK):
            msg=_('The %s file does not have read permission.' % logfile)
            raise UserError(_(msg))
        selfTotal=0
        selfLinesFound=''
        to_date=fields.Date.today()
        nameFile=''
        for record in self.resolved_queries_ids:
            if record.search_parameter:
                nameFile+=record.model_id.name[0]
                model=self.env[record.model_id.model]
                self.total_row=model.search_count([])
                patron=re.compile(record.search_parameter)
                linesFound=''
                total=0
                cant=0
                with open(logfile, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        total+=1
                        match = patron.search(line)
                        if match:
                            cant+=1
                            linesFound+='N-%s:L-%s:%s' %(str(cant),str(total),line)
                if linesFound:
                    selfLinesFound+=linesFound
                    record.query_file = base64.b64encode(bytes(linesFound, 'utf-8'))
                    record.store_fname="%s_%s_t_%s.txt" %(nameFile,to_date,str(cant))
                else:
                    record.query_file = ''
                    record.store_fname=''
                record.total=cant
                selfTotal+=cant
        if selfLinesFound:
            self.total=selfTotal
            self.query_file = base64.b64encode(bytes(selfLinesFound, 'utf-8'))
            self.store_fname="%s_%s_t_%s.txt" %(record.model_id.name,to_date,str(selfTotal))
        return {
        'context': self.env.context,
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': self._name,
        'res_id': self.id,
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target': 'new'}

class CargarDataWizard(models.TransientModel):
    """ Run resolved queries wizard. """
    _name = 'resolved.queries.data.wizard'
    _description = 'Run resolved queries wizard'

    FieldsR=["id","prefix","model_id/id","search_parameter"]
    Data=[
        ["__export__.resolved_queries_8_6ce8e604","SELECT","base.model_ir_ui_view",'SELECT\s\"ir_ui_view\"']
        ]
    def _default_get_log_level(self):
        return tools.config.get('log_level')
     #~ parametro de configuracion del nivel del Log
    log_level = fields.Char(
                        string='Log level',
                        readonly=True,
                        default=_default_get_log_level,
                        help="""Log level configuration parameter,
                        To test the modules of go ui view cache, web base cache or website
                        base cache, you must change the log_leve parameter in the configuration
                        file to debug_sql""")

    @api.multi
    def data_ir_ui_cache(self):
        r=self.env['resolved.queries']
        result=r.load(self.FieldsR,self.Data)
        return {
        'context': self.env.context,
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': r._name,
        'res_id': result['ids'][0],
        'view_id': False,
        'type': 'ir.actions.act_window'
            }


    @api.multi
    def data_web_base_cache(self):
        r=self.env['resolved.queries']
        IrModelData = self.env['ir.model.data']
        IrModelRecord = IrModelData.get_object('resolved_queries', 'resolved_queries_action_window')
        action=IrModelRecord.read(['name', 'view_mode', 'res_model', 'target', 'type', 'view_mode'])
        data=[
            ["__export__.resolved_queries_8_6ce8e604","SELECT","base.model_ir_ui_view",'SELECT\s\"ir_ui_view\"'],
            ["__export__.resolved_queries_112_66ce8e604","SELECT","base.model_ir_actions_actions",'SELECT\s\"ir_actions\"'],
            ["__export__.resolved_queries_113_76ce8e604","SELECT","base.model_ir_actions_act_window_view",'SELECT\s\"ir_act_window_view\"'],
            ["__export__.resolved_queries_114_86ce8e604","SELECT","base.model_ir_translation",'SELECT\s\"ir_translation\"'],
            ["__export__.resolved_queries_115_96ce8e604","SELECT","base.model_ir_ui_menu",'SELECT\s\"ir_ui_menu\"'],
            ["__export__.resolved_queries_116_06ce8e604","SELECT","base.model_res_company",'SELECT\s\"res_company\"'],
            ["__export__.resolved_queries_117_77ce8e604","SELECT","base.model_res_lang",'SELECT\s\"res_lang\"']
            ]
        result=r.load(self.FieldsR,data)
        if not action:
            action = {}
        else:
            action = action[0]
        return action

    @api.multi
    def data_website_base_cache(self):
        r=self.env['resolved.queries']
        IrModelData = self.env['ir.model.data']
        IrModelRecord = IrModelData.get_object('resolved_queries', 'resolved_queries_action_window')
        action=IrModelRecord.read(['name', 'view_mode', 'res_model', 'target', 'type', 'view_mode'])
        data=[
            ["__export__.resolved_queries_8_6ce8e604","SELECT","base.model_ir_ui_view",'SELECT\s\"ir_ui_view\"'],
            ["__export__.resolved_queries_112_66ce8e604","SELECT","base.model_ir_actions_actions",'SELECT\s\"ir_actions\"'],
            ["__export__.resolved_queries_113_76ce8e604","SELECT","base.model_ir_actions_act_window_view",'SELECT\s\"ir_act_window_view\"'],
            ["__export__.resolved_queries_114_86ce8e604","SELECT","base.model_ir_translation",'SELECT\s\"ir_translation\"'],
            ["__export__.resolved_queries_115_96ce8e604","SELECT","base.model_ir_ui_menu",'SELECT\s\"ir_ui_menu\"'],
            ["__export__.resolved_queries_116_06ce8e604","SELECT","base.model_res_company",'SELECT\s\"res_company\"'],
            ["__export__.resolved_queries_117_77ce8e604","SELECT","base.model_res_lang",'SELECT\s\"res_lang\"'],
            ["__export__.resolved_queries_118_9877ce8e604","SELECT","website.model_website",'SELECT\s\"website\"'],
            ["__export__.resolved_queries_119_897ce8e604","SELECT","website.model_website_menu",'SELECT\s\"website_menu\"']
            ]
        result=r.load(self.FieldsR,data)
        if not action:
            action = {}
        else:
            action = action[0]
        return action
