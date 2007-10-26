# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.web.chrome import Chrome, add_stylesheet, add_script
from trac.util.html import html

from tracteamroster.api import UserProfilesSystem, UserProfile

class TeamRosterMacro(WikiMacroBase):
    """Returns project's team roster.
        
    Usage:
        {{{ 
        
        [[TeamRoster]]                                    # Without arguments returns current active user profiles (with enabled='1')
        [[TeamRoster(role='developer', enabled='1')]]     # Returns all userProfiles with role='developer' and enabled='1'
        [[TeamRoster(name='%someName%')]]                 # Returns all userProfiles with name like 'someName' 
        [[TeamRoster({id='cbalan'},{role='%arh%'})]]      # Returns cbalan's profile and user profiles with role='%arh%' 
        [[TeamRoster(|class=someCSS_Class, style=border:1px solid green;padding:12px)]] # Adds style and class attributes to box layout 
        
        }}}
    """
    
    
    def expand_macro(self, formatter, name, content):
        
        teamRosterData=dict(userProfiles=[])
        rendered_result=""
        contentArgs={}
        layoutArgs={}
        userProfileTemplates=[]     
       
        # collecting arguments
        if content:    
            for i, macroArgs in enumerate( content.split('|') ):
                if i == 0:
                    contentArgs = MacroArguments( macroArgs )
                    self.log.error(contentArgs)
                    continue
                if i == 1: 
                    layoutArgs = MacroArguments( macroArgs )
                    break
            
            # extracting userProfile attrs 
            if len(contentArgs)>0:
                userProfileTemplates.append(UserProfile(**contentArgs))
                
            if len(contentArgs.getListArgs())>0:
                for listItem in contentArgs.getListArgs():
                    userProfileTemplates.append(UserProfile( **MacroArguments(listItem[1:len(listItem)-1])))
            
        # _fixes
        def _fixes(userProfile):
            userProfile.bio_html = wiki_to_html(userProfile.bio, self.env, formatter.req) or "[blank]"
            return userProfile
        
        # grabbing userProfiles
        if len(userProfileTemplates)>0:              
            teamRosterData['userProfiles'] = map(_fixes,UserProfilesSystem(self.env).search_userProfile(userProfileTemplates))
        else:
            teamRosterData['userProfiles'] = map(_fixes,UserProfilesSystem(self.env).get_active_userProfiles())
        
        # add stylesheet&script
        add_stylesheet(formatter.req,'tracteamroster/css/teamroster.css')
        add_script(formatter.req,'tracteamroster/js/teamroster.js')
        
        # render template
        rendered_result = Chrome(self.env).render_template(formatter.req, 'macro_teamroster_team.html', {'teamRoster':teamRosterData}, fragment=True)
            
        # wrap everything 
        if len(layoutArgs)>0:
            rendered_result= html.div(rendered_result, **layoutArgs)

        return rendered_result

    

class MacroArguments(dict):
    
    largs=[]

    def __init__(self, arguments):
        self.largs, kwargs = parse_args(arguments)
        for k,v in kwargs.items():
            self[str(k)]=v
    
    def getListArgs(self):
        return self.largs
        
    def getInt(self, name, default=None):    
        value = self.get(name, default)
        if value == '':
            return default
        try:
            return int(value)
        except Exception, e:
            return default
    
    def getList(self, name, default=None):
        value = self.get(name, default)
        try:
            return value.split(',')
        except Exception, e:
            return defaultValue
    
    def getDict(self, name, default=None):
        value = self.get(name, default)
        if value.startswith('{') and value.endswith('}'):
            return MacroArguments(value[1:len(value)-1])
    