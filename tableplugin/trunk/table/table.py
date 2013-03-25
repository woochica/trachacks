#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 author <author_email>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# system imports
import os
import re
import inspect
from uuid import uuid4

# trac imports
from trac.core import *
from trac.util.html import Markup
from trac.wiki import format_to_html, format_to_oneliner
from trac.wiki import WikiPage
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.parser import WikiParser

# genshi imports
from genshi.builder import tag

# to match any of the following:
# @css style1: DATA
# @column heading1 (style1): DATA
# @column heading2: DATA
# @heading1: DATA
# @heading2 (style1): DATA
ATTRIBUTE_REGEX = re.compile('^@([^@\s\:]+)\s*(?:([^\s\(\)\:]+))?\s*(?:\(([^\s\:]+)\))?(?:\:\s*(.*))?', re.I)


class StyledTablePlugin(Component):

    CONFIG_KEY = 'styledtable'
    DESC_KEY   = '.description'

    implements(IWikiMacroProvider)

    def __init__(self):
        """
        Read the config for options on __init__
        """
        self.CONFIG = {}
        self.DESC   = {}
        conf = self.env.config
        for key, ignored in conf.options(self.CONFIG_KEY):
            if key.endswith(self.DESC_KEY):
                continue
            cols = conf.getlist(self.CONFIG_KEY, key)
            self.CONFIG[key] = self._parse_config(cols)
            self.DESC  [key] = conf.get(self.CONFIG_KEY, key+self.DESC_KEY) 

    # methods for IWikiMacroProvider

    def get_macros(self):
        """
        An iterable that provides the name of the
        provided macro.
        """
        yield self.CONFIG_KEY
        for key in self.CONFIG.keys():
            yield key

    def get_macro_description(self, name):
        """
        Returns a plaintext description of the macro.
        """
        if name == self.CONFIG:
            return inspect.getdoc(self.__class__)

        doc = self.DESC[name] + '\n'
        doc += " || '''Column Name''' || '''Aliases''' || \n"
        for desc, keys in self.CONFIG[name]:
            doc += ' || ' + desc + ' || ' + ', '.join(keys) + ' || \n'
        return doc

    def expand_macro(self, formatter, name, args):
        """
        Called by the formatter to render the parsed
        wiki text.
        """

        def to_html(text):
            """
            Format the parsed text from the rows into HTML.
            """
            if not text:
                return ''

            # simple check to determine whether format_to_html or 
            # format_to_oneliner should be used. If there are multiple
            # lines, use format_to_html, otherwise use format_to_oneliner

            stripped_text = text.strip()
            splitlines = stripped_text.splitlines()

            if len(splitlines) > 1:
                formatted_text = format_to_html(self.env, formatter.context, text)
            else:
                formatted_text = '<br />'.join( [format_to_oneliner(self.env, formatter.context, line) \
                    for line in text.splitlines()] ) 
            return Markup( formatted_text )

        if not args:
            return Markup()

        # use the formatter to find the TablePluginStyles
        if not formatter.wiki.has_page('TablePluginStyles'):
            # if our
            build_table_plugin_styles_page(self.env)

        if formatter.wiki.has_page('TablePluginStyles'):
            # at this point, the new style page should exist
            # so use the styles defined there.
            config_args = self._parse_wiki_style_page(self.env)
        else:
            # nice error handling in here possible incase
            # the page cannot be created for whatever reason?
            pass

        config_table_styles, config_css_styles = self._parse_styles(config_args)

        args_table_styles, args_css_styles = self._parse_styles(args)
        global_css_styles = dict(config_css_styles.items() + args_css_styles.items())

        column_list = []
        row_count = 0

        row_dict = {}
        row_list = []

        heading = False
        body_name = ''
        heading_set = False
        body_set_first = False
        first_row_as_header = False
        is_row = False

        table_id = ''
        table_data = ''

        table_style = ''
        column_style_dict = {}

        for attribute in self._parse_args(args):
            if 'table' in attribute:
                # get the table id to use
                table_id = attribute['table']['name']
                table_data = attribute['table']['data']
                table_style = attribute['table']['style'].replace('@', '')
            elif 'css' in attribute:
                pass
            elif 'column' in attribute:
                column_name = attribute['column']['name']
                column_list.append(column_name)
                if attribute['column']['style']:
                    column_style_dict[column_name] = attribute['column']['style']
            elif 'header' in attribute:
                heading = True
                heading_set = True
            elif 'body' in attribute:
                body_name = str(uuid4())
                if not heading_set and not first_row_as_header:
                    body_set_first = True
                heading = False
            elif 'row' in attribute:
                is_row = True
                row_count = 0
                row_style = attribute['row']['style']
            else:
                if not heading_set and not body_set_first:
                    first_row_as_header = True
                for key, value in attribute.items():
                    value['heading'] = heading
                    if body_name:
                        value['body_name'] = body_name
                    if is_row:
                        # if its a row, apply row style
                        original_style = value['style']
                        value['style'] = ' '.join([original_style, row_style])
                if row_count == (len(column_list) - 1):
                    row_dict.update(attribute)
                    row_list.append(row_dict)
                    row_dict = {}
                    row_count = 0
                    is_row = False
                else:
                    row_dict.update(attribute)
                    row_count += 1

        thead = tag.thead()
        for row in row_list:
            if body_set_first:
                break
            header_row = tag.tr()
            for column in column_list:
                header_cell = ''
                if row[column]['heading'] or first_row_as_header:
                    header_cell = tag.th()
                    header_cell(to_html(row[column]['data']), class_=row[column]['style'].replace('@', ''))
                    header_row(header_cell)
            if header_cell:
                thead(header_row)
            if first_row_as_header:
                break

        if table_style:
            table_id = table_style
            table_data = config_table_styles[table_style]['data']


        css_data = self._build_css_template(global_css_styles)

        full_style_data = ''
        full_style_data += table_data
        full_style_data += css_data

        tstyle = tag.style()
        tstyle = tag.style(full_style_data)

        tbody = tag.tbody()
        body_name = ''
        body_set = False

        tbody_list = []
        for row in row_list:
            if first_row_as_header:
                heading_set = False
                first_row_as_header = False
                continue
            trow = tag.tr()
            tcol = ''
            for column in column_list:
                if row[column]['heading']:
                    continue
                if row[column]['body_name'] == body_name and not body_set:
                    body_set = True
                elif row[column]['body_name'] != body_name and not body_set:
                    body_name = row[column]['body_name']
                    body_set = True
                elif row[column]['body_name'] != body_name and body_set:
                    tbody_list.append(tbody)
                    tbody = tag.tbody()
                    trow = tag.tr()
                    body_name = row[column]['body_name']
                tcol = tag.td()
                # if there is a column style available,
                # add it to what is already there
                formatted_column_style = ''
                if column in column_style_dict:
                    column_style = column_style_dict[column].replace('@', '')
                    formatted_column_style = column_style.replace(';', ' ')
                class_styles = row[column]['style'].replace('@', '')
                formatted_class_styles = class_styles.replace(';', ' ')
                formatted_item = ' '.join([formatted_class_styles, formatted_column_style])
                tcol(to_html(row[column]['data']), class_=formatted_item)
                trow(tcol)
            if tcol:
                tbody(trow)
        tbody_list.append(tbody)

        return tag.table([tstyle, thead, tbody_list], class_=table_id)

    # helper methods
    
    def _read_config(self):

        trac_root = self.env.path
        style_conf_path = os.path.join(trac_root, 'htdocs', 'style.conf')

        with open(style_conf_path) as style_conf:
            style_args = style_conf.read()
        return style_args

    def _parse_styles(self, args):
        # firstly, check for any custom definitions, otherwise
        # use the defaults

        table_dict = {}
        css_dict = {}

        for attribute in self._parse_args(args):
            if 'table' in attribute:
                table_name = attribute['table']['name']
                table_style = attribute['table']['style']
                table_data = attribute['table']['data']
                table_dict[table_name] = {}
                table_dict[table_name]['style'] = table_style
                table_dict[table_name]['data'] = table_data

            elif 'css' in attribute:
                css_name = attribute['css']['name']
                css_data = attribute['css']['data']
                css_dict[css_name] = {}
                css_dict[css_name]['data'] = css_data

        return table_dict, css_dict

    def _build_css_template(self, css_dict):
        css_template = ''
        # build up the css
        for key, value in css_dict.items():
            class_name = key
            css_data = value['data']
            css_template += "\n.%s {\n %s \n}\n" % (class_name, css_data)
        return css_template

    def _parse_args(self, args):
        get_data = False
        is_code_block = False
        attribute_dict = {}
        macro_block = False
        block_check = False
        for line in args.splitlines():
            # ignore all comment lines
            if line.strip().startswith('#!') and not is_code_block:
                continue

            attribute_match = ATTRIBUTE_REGEX.match(line)
            if attribute_match and not is_code_block:
                if attribute_dict:
                    yield attribute_dict
                    attribute_dict = {}
                    get_data = False
                    is_code_block = False
                type_match = attribute_match.group(1)
                attribute_dict[type_match] = {}
                attribute_dict[type_match]['name'] = attribute_match.group(2)
                attribute_dict[type_match]['style'] = attribute_match.group(3) or ''
                attribute_dict[type_match]['data'] = attribute_match.group(4) or ''
                attribute_dict[type_match]['heading'] = False
                attribute_dict[type_match]['body_name'] = ''
                get_data = True
                continue

            if is_code_block == False and re.match(r'^\s*{{{\s*$', line):
                is_code_block = True
                value = attribute_dict[type_match]['data']
                attribute_dict[type_match]['data'] = value + '\n' + line
                continue
            elif is_code_block == True and re.match(r'^\s*}}}\s*$', line):
                is_code_block = False
                value = attribute_dict[type_match]['data']
                attribute_dict[type_match]['data'] = value + '\n' + line
                continue

            # if a code block is found, it will only be after other
            # options have been set as part of the row. therefore
            # these attributes will always be available.
            if is_code_block:
                value = attribute_dict[type_match]['data']
                attribute_dict[type_match]['data'] = value + '\n' + line
                continue 

            if get_data and not is_code_block:
                if not line.strip():
                    value = attribute_dict[type_match]['data']
                    attribute_dict[type_match]['data'] = value + '\n'
                    continue
                else:
                    value = attribute_dict[type_match]['data']
                    attribute_dict[type_match]['data'] = value + '\n' + line
                    continue
        yield attribute_dict

    def _parse_wiki_style_page(self, env):
        # Load the TablePluginStyles WikiPage and obtain
        # the text contained. The style definitions will
        # be contained within a code-block, so we should
        # check between any instances of {{{ and }}}, 
        # ignoring any macro/plugin blocks that contain 
        # headers of the following type: #!<name>

        new_styles = WikiPage(env, 'TablePluginStyles')

        style_args = new_styles.text

        complete_code_block = ''
        block_check = False
        for line in style_args.splitlines():
            if re.match(r'^\s*{{{\s*$', line) and not block_check:
                # Find {{{ Check for #!<name>
                block_check = True
                continue
            if re.match(r'^\s*}}}\s*$', line) and block_check:
                # when }}} found, reset
                block_check = False
                continue
            if block_check and re.match(r'^#!\w*$', line):
                # #!<name> found, skipping block.
                block_check = False
                continue
            if block_check and not re.match(r'^#!\w*$', line):
                # codeblock found, adding line: %s" % line
                complete_code_block += '\n'+line
                continue

        return complete_code_block

def build_table_plugin_styles_page(env):
    table_plugin_style_page = WikiPage(env, 'TablePluginStyles')
    table_plugin_style_page.text = \
"""
== Location for !TablePlugin Style Definitions ==

Define the table styles and CSS styles below in a codeblock.

{{{
@table default:

table.default {
    font-family: verdana,arial,sans-serif;
    font-size:11px;
    color:#333333;
    border-width: 1px;
    border-color: #666666;
    border-collapse: collapse;
    }

table.default thead th {
    border-width: 1px;
    padding: 2px;
    border-style: solid;
    border-color: #666666;
    background-color: #dedede;
    }

table.default tbody td {
    border-width: 1px;
    padding: 2px;
    border-style: solid;
    border-color: #666666;
    background-color: #ffffff;
    }

@css header:
   font-weight: bold;
   text-align: center;
}}}

----

An example of a table styled using the above would look like the following:

{{{
#!table

@table mytable (@default):

@column number
@column item
@column width
@column height

@row (@header)
@number: Number
@item: Item
@width: Width
@height: Height

@number: 1
@item: Item 1
@width: 10
@height: 10

@number: 2
@item: Item 2
@width: 20
@height: 20

@number: 3
@item: Item 3
@width: 30
@height: 30

@number: 4
@item: Item 4
@width: 40
@height: 40

}}}

"""
    try:
        table_plugin_style_page.save('TablePlugin',
                                     'Creating default styles for !TablePlugin',
                                     table_plugin_style_page.resource.id,
                                     )
    except:
        # For some reason, we get an error about
        # saving the page, not sure why?
        pass
