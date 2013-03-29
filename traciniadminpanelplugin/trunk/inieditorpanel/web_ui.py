import re
import copy

from pkg_resources import resource_filename

from trac.core import *
from trac.config import ConfigSection, Option, ListOption, ExtensionOption, _TRUE_VALUES
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, add_notice, add_warning
from trac.admin.api import IAdminPanelProvider
from trac.wiki.formatter import format_to_oneliner
from trac.mimeview.api import Context

from genshi.template import TemplateLoader
from genshi.template.text import NewTextTemplate

from inieditorpanel.api import *

from trac.util.translation import dgettext, domain_functions

_, tag_, N_, add_domain, gettext = domain_functions(
    'inieditorpanel', 
    ('_', 'tag_', 'N_', 'add_domain', 'gettext'))


class TracIniAdminPanel(Component):
  """ An editor panel for trac.ini. """

  implements(IAdminPanelProvider, ITemplateProvider)
  
  valid_section_name_chars = Option('ini-editor', 'valid-section-name-chars', '^[a-zA-Z0-9\\-_\\:]+$',
      doc="""Defines the valid characters for a section name or option name in 
      `trac.ini`. Must be a valid regular expression. You only need to change 
      these if you have plugins that use some strange section or option names.
      """, doc_domain="inieditorpanel")
  
  valid_option_name_chars = Option('ini-editor', 'valid-option-name-chars', '^[a-zA-Z0-9\\-_\\:.]+$',
      doc="""Defines the valid characters for a section name or option name in 
      `trac.ini`. Must be a valid regular expression. You only need to change 
      these if you have plugins that use some strange section or option names.
      """, doc_domain="inieditorpanel")
      
  security_manager = ExtensionOption('ini-editor', 'security-manager', 
      IOptionSecurityManager, 'IniEditorEmptySecurityManager',
      doc="""Defines the security manager that specifies whether the user has 
      access to certain options.
      """, doc_domain="inieditorpanel")
  
  # See "IniEditorBasicSecurityManager" for why we use a pipe char here.
  password_options = ListOption('ini-editor', 'password-options',
      doc="""Defines option fields (as `section-name|option-name`) that 
      represent passwords. Password input fields are used for these fields.
      Note the fields specified here are taken additionally to some predefined 
      fields provided by the ini editor.
      """, doc_domain="inieditorpanel")
      
  DEFAULT_PASSWORD_OPTIONS = {
      'notification|smtp_password': True
    }
  
  def __init__(self):
    """Set up translation domain"""
    locale_dir = resource_filename(__name__, 'locale')
    add_domain(self.env.path, locale_dir)

    self.valid_section_name_chars_regexp = re.compile(self.valid_section_name_chars)
    self.valid_option_name_chars_regexp = re.compile(self.valid_option_name_chars)
    
    self.password_options_set = copy.deepcopy(self.DEFAULT_PASSWORD_OPTIONS)
    for option in self.password_options:
      self.password_options_set[option] = True

  #
  # IAdminPanelProvider methods
  #

  def get_admin_panels(self, req):
    if 'TRAC_ADMIN' in req.perm:
      yield ('general', dgettext('messages', 'General'), 'trac_ini_editor', _('trac.ini Editor'))

  def render_admin_panel(self, req, cat, page, path_info):  
    req.perm.require('TRAC_ADMIN')

    if path_info == None:
      ext = ""
    else:
      ext = '/' + path_info

    #
    # Gather section names for section drop down field
    #
    all_section_names = [ ]
    for section_name in self.config.sections():
      if section_name == 'components':
        continue
      all_section_names.append(section_name)

    # Check whether section exists and if it's not existing then check whether
    # its name is a valid section name.
    if (path_info is not None) and (path_info not in ('', '/', '_all_sections')) \
       and (path_info not in all_section_names):
      if path_info == 'components':
        add_warning(req, _('The section "components" can\'t be edited with the ini editor.'))
        req.redirect(req.href.admin(cat, page))
        return None
      elif self.valid_section_name_chars_regexp.match(path_info) is None:
        add_warning(req, _('The section name %s is invalid.') % path_info)
        req.redirect(req.href.admin(cat, page))
        return None
        
      # Add current section if it's not already in the list. This happens if
      # the section is essentially empty (i.e. newly created with no non-default
      # option values and no option from the option registry).
      all_section_names.append(path_info)

    registry = ConfigSection.get_registry(self.compmgr)
    descriptions = { }
    for section_name, section in registry.items():
      if section_name == 'components':
        continue
      doc = section.__doc__
      if not section_name in all_section_names:
        all_section_names.append(section_name)
      if doc:
        doc = dgettext(section.doc_domain, doc)
        format_to_oneliner(self.env, Context.from_request(req), doc)
        descriptions[section_name] = doc

    all_section_names.sort()
        
    sections = {}
    
    #
    # Check security manager
    #
    manager = None
    try:
      manager = self.security_manager
    except Exception, detail:  # "except ... as ..." is only available since Python 2.6
      if req.method != 'POST':
        # only add this warning once
        add_warning(req, _('Security manager could not be initated. %s') % unicode(detail))

    if manager is None:
      #
      # Security manager is not available
      #
      if req.method == 'POST':
        req.redirect(req.href.admin(cat, page) + ext)
        return None

    elif req.method == 'POST' and 'change-section' in req.args:
      # 
      # Changing the section
      #
      req.redirect(req.href.admin(cat, page) + '/' + req.args['change-section'])
      return None
        
    elif req.method == 'POST' and 'new-section-name' in req.args:
      #
      # Create new section (essentially simply changing the section)
      #
      section_name = req.args['new-section-name'].strip()
      
      if section_name == '':
        add_warning(req, _('The section name was empty.'))
        req.redirect(req.href.admin(cat, page) + ext)
      elif section_name == 'components':
        add_warning(req, _('The section "components" can\'t be edited with the ini editor.'))
        req.redirect(req.href.admin(cat, page))
      elif self.valid_section_name_chars_regexp.match(section_name) is None:
        add_warning(req, _('The section name %s is invalid.') % section_name)
        req.redirect(req.href.admin(cat, page) + ext)
      else:
        if section_name not in all_section_names:
          add_notice(req, _('Section %s has been created. Note that you need to add at least one option to store it permanently.') % section_name)
        else:
          add_warning(req, _('The section already exists.'))
        req.redirect(req.href.admin(cat, page) + '/' + section_name)
      
      return None
    
    elif path_info is not None and path_info not in ('', '/'):
      #
      # Display and possibly modify section (if one is selected)
      #
      default_values = self.config.defaults()
      
      # Gather option values
      # NOTE: This needs to be done regardless whether we have POST data just to
      #   be on the safe site.
      if path_info == '_all_sections':
        # All sections
        custom_options = self._get_session_custom_options(req)
        # Only show sections with any data
        for section_name in all_section_names:
          sections[section_name] = self._read_section_config(req, section_name, default_values, custom_options)
      else:
        # Only a single section
        # Note: At this point path_info has already been verified to contain a 
        #   valid section name (see check above).
        sections[path_info] = self._read_section_config(req, path_info, default_values)
      

      #
      # Handle POST data
      #
      if req.method == 'POST':
        # Overwrite option values with POST values so that they don't get lost
        for key, value in req.args.items():
          if not key.startswith('inieditor_value##'): # skip unrelated args
            continue
         
          name = key[len('inieditor_value##'):].split('##')
          section_name = name[0].strip()
          option_name = name[1].strip()
          
          if section_name == 'components':
            continue
          
          if option_name == 'dummy':
            if section_name not in sections:
              sections[section_name] = { }
            continue

          section = sections.get(section_name, None)
          if section:
            option = section.get(option_name, None)
            if option:
              self._set_option_value(req, section_name, option_name, option, value)
            else:
              # option not available; was propably newly added
              section[option_name] = self._create_new_field_instance(req, section_name, option_name, default_values.get(section_name, None), value)
          else:
            # newly created section (not yet stored)
            sections[section_name] = { option_name: self._create_new_field_instance(req, section_name, option_name, None, value) }
            
        
        # Check which options use their default values
        # NOTE: Must be done after assigning field value from the previous step
        #   to ensure that the default value has been initialized.
        if 'inieditor_default' in req.args:
          default_using_options = req.args.get('inieditor_default')
          if default_using_options is None or len(default_using_options) == 0:
            # if no checkbox was selected make this explicitly a list (just for safety)
            default_using_options = [ ]
          elif type(default_using_options).__name__ != 'list':
            # if there's only one checkbox it's just a string
            default_using_options = [ unicode(default_using_options) ] 
          
          for default_using_option in default_using_options:
            name = default_using_option.split('##')
            section_name = name[0].strip()
            option_name = name[1].strip()
            section = sections.get(section_name, None)
            if section:
              option = section.get(option_name, None)
              if option:
                if option['access'] == ACCESS_MODIFIABLE:
                  option['value'] = option['default_value']
              else:
                # option not available; was propably newly added
                section[option_name] = self._create_new_field_instance(req, section_name, option_name, default_values.get(section_name, None))
            else:
              # newly created section (not yet stored)
              sections[section_name] = { option_name: self._create_new_field_instance(req, section_name, option_name, None) }
        
        
        #
        # Identify submit type
        # NOTE: Using "cur_focused_field" is a hack to support hitting the 
        #  return key even for the new-options field. Without this hitting 
        #  return would always associated to the apply button.
        #
        submit_type = None
        cur_focused_field = req.args.get('inieditor_cur_focused_field', '')
        if cur_focused_field.startswith('option-value-'):
          submit_type = 'apply-' + cur_focused_field[len('option-value-'):]
        elif cur_focused_field.startswith('new-options-'):
          submit_type = 'addnewoptions-' + cur_focused_field[len('new-options-'):]
        else:
          for key in req.args:
            if not key.startswith('inieditor-submit-'):
              continue
              
            submit_type = key[len('inieditor-submit-'):]
            break
       
        if submit_type.startswith('apply'): # apply changes
          if submit_type.startswith('apply-'):
            # apply only one section
            section_name = submit_type[len('apply-'):].strip()
            if self._apply_section_changes(req, section_name, sections[section_name]):
              add_notice(req, _('Changes for section %s have been applied.') % section_name)
              self.config.save()
            else:
              add_warning(req, _('No changes have been applied.'))
          else:
            # apply all sections
            changes_applied = False
            for section_name, options in sections.items():
              if self._apply_section_changes(req, section_name, options):
                changes_applied = True
            
            if changes_applied:
              add_notice(req, _('Changes have been applied.'))
              self.config.save()
            else:
              add_warning(req, _('No changes have been applied.'))

        elif submit_type.startswith('discard'):
          if submit_type.startswith('discard-'):
            # discard only one section
            section_name = submit_type[len('discard-'):].strip()
            self._discard_section_changes(req, section_name, sections[section_name])
            add_notice(req, _('Your changes for section %s have been discarded.') % section_name)
          else:
            # discard all sections
            for section_name, options in sections.items():
              self._discard_section_changes(req, section_name, options)
            add_notice(req, _('All changes have been discarded.'))
        
        elif submit_type.startswith('addnewoptions-'):
          section_name = submit_type[len('addnewoptions-'):].strip()
          section = sections[section_name]
          new_option_names = req.args['new-options-' + section_name].split(',')
          section_default_values = default_values.get(section_name, None)
          
          field_added = False
          for new_option_name in new_option_names:
            new_option_name = new_option_name.strip()
            if new_option_name in section:
              continue # field already exists
            
            if self.valid_option_name_chars_regexp.match(new_option_name) is None:
              add_warning(req, _('The option name %s is invalid.') % new_option_name)
              continue
              
            new_option = self._create_new_field_instance(req, section_name, new_option_name, section_default_values)
            if new_option['access'] != ACCESS_MODIFIABLE:
              add_warning(req, _('The new option %s could not be added due to security restrictions.') % new_option_name)
              continue
            
            self._add_session_custom_option(req, section_name, new_option_name)
            field_added = True
          
          if field_added:
            add_notice(req, _('The new fields have been added to section %s.') % section_name)
          else:
            add_warning(req, _('No new fields have been added.'))
        
        req.redirect(req.href.admin(cat, page) + ext)
        return None
    
    # Split sections dict for faster template rendering
    modifiable_options = { }
    readonly_options = { }
    hidden_options = { }
    for section_name, options in sections.items():
      sect_modifiable = { }
      sect_readonly = { }
      sect_hidden =  { }
      for option_name, option in options.items():
        if option['access'] == ACCESS_MODIFIABLE:
          sect_modifiable[option_name] = option
        elif option['access'] == ACCESS_READONLY:
          sect_readonly[option_name] = option
        else:
          sect_hidden[option_name] = option
      
      modifiable_options[section_name] = sect_modifiable
      readonly_options[section_name] = sect_readonly
      hidden_options[section_name] = sect_hidden

    registry = ConfigSection.get_registry(self.compmgr)
    descriptions = { }
    for name, section in registry.items():
      doc = section.__doc__
      if doc:
        doc = dgettext(section.doc_domain, doc)
        format_to_oneliner(self.env, Context.from_request(req), doc)
        descriptions[name] = doc
    
    data = { 'all_section_names': all_section_names, 
             'sections' : sections,
             'descriptions' : descriptions,
             'modifiable_options': modifiable_options,
             'readonly_options': readonly_options,
             'hidden_options': hidden_options
           }

    data['_'] = _
    data['gettext'] = gettext

    # Parse the JavaScript code
    # NOTE: We can't use <xi:include> for this as Genshi escapes XML characters
    #   in the JavaScript code leading invalid variable values (that contain
    #   for example '>') in some cases.    
    jsLoader = TemplateLoader(self.get_templates_dirs(), auto_reload=self.config.getbool('trac', 'auto_reload'))
    jsTmpl = jsLoader.load('editor-data.js', cls=NewTextTemplate)
    data['javascript'] = jsTmpl.generate(**data).render(encoding=None) # pass data dict as kwargs
    
    add_stylesheet(req, 'inieditorpanel/main.css')
    add_script(req, 'inieditorpanel/editor.js')
    return 'admin_tracini.html', data
    
  def _get_session_value(self, req, section_name, option_name):
    """ Returns the value for an unsaved option stored in the current session,
        if it exists. Values get removed here when they're saved/applied.
    """
    name = 'inieditor|%s|%s' % (section_name, option_name)
    if name in req.session:
      return True, req.session[name]
    else:
      return False, None
    
  def _set_session_value(self, req, section_name, option_name, option_value):
    """ Stores the value of an unsaved option in the current session. """
    name = 'inieditor|%s|%s' % (section_name, option_name)
    req.session[name] = option_value
      
  def _remove_session_value(self, req, section_name, option_name):
    """ Removes the value of an unsaved option from the current session. """
    name = 'inieditor|%s|%s' % (section_name, option_name)
    if name in req.session:
      del req.session[name]
      
  def _add_session_custom_option(self, req, section_name, option_name):
    """ Used to remember a custom (new) option which isn't backed by 
        "Option.registry". Without storing it here, such options would be
        lost when using "req.redirect()".
    """
    name = 'inieditor-custom|%s|%s' % (section_name, option_name)
    req.session[name] = True
    
  def _get_session_custom_options(self, req, filter_section_name = None):
    """ Retrieves the remembered custom (new) options. If "filter_section_name"
        is None, the options for all sections will be returned. Otherwise only
        the options for the specified section will be returned.
    """
    sections = { }
    for item_name in req.session.keys():
      if not item_name.startswith('inieditor-custom|'):
        continue
        
      parts = item_name.split('|', 3)
      if len(parts) < 3:
        continue
        
      section_name = parts[1]
      option_name = parts[2]
      
      if filter_section_name is not None and section_name != filter_section_name:
        continue
        
      if section_name in sections:
        sections[section_name][option_name] = True
      else:
        sections[section_name] = { option_name: True }
        
    return sections
    
  def _remove_session_custom_option(self, req, section_name, option_name):
    name = 'inieditor-custom|%s|%s' % (section_name, option_name)
    if name in req.session:
      del req.session[name]
    
  def _read_section_config(self, req, section_name, default_values, custom_options = None):
    """ Gathers all existing information about the specified section. Retrieves
        this information from "self.config" (stored options and options from the
        registry) and from the session (new, custom options).
    """
    def _assemble_option(option_name, stored_value):
      option = self._gather_option_data(req, section_name, option_name, section_default_values)
      stored_value = self._convert_value(stored_value, option['option_info'])

      does_exist, value = self._get_session_value(req, section_name, option_name)
      if does_exist:
        option['value'] = value
      else:
        option['value'] = stored_value
      
      option['stored_value'] = stored_value
      return option
    
    options = {}
    section_default_values = default_values.get(section_name, None)

    for option_name, stored_value in self.config.options(section_name):
      options[option_name] = _assemble_option(option_name, stored_value)
      
    if custom_options is None:
      custom_options = self._get_session_custom_options(req, section_name)
    
    if section_name in custom_options:
      for option_name in custom_options[section_name].keys():
        if option_name in options:
          continue
        
        options[option_name] = _assemble_option(option_name, None)
      
    return options
    
  def _convert_value(self, value, option = None):
    """ Converts a config value into a string so that it can be used by Genshi
        without needing to convert or escape anything.
    """
    if option is not None:
      option_type = option.__class__.__name__
      if option_type == 'BoolOption':
        if str(value).lower() in _TRUE_VALUES:
          return 'true'
        else:
          return 'false'
      elif (option_type == 'ListOption' or option_type == 'OrderedExtensionsOption') and type(value).__name__ == 'list':
        return unicode(option.sep).join(value)
    
    if value is None:
      return ''
    
    return unicode(value)
    
  def _gather_option_data(self, req, section_name, option_name, section_default_values):    
    option = None
    if (section_name, option_name) in Option.registry:
      # Allow wiki formatting in descriptions
      option = Option.registry[(section_name, option_name)]
      doc = dgettext(option.doc_domain, option.__doc__)
      option_desc = format_to_oneliner(self.env, Context.from_request(req), doc)
      option_type = option.__class__.__name__.lower()[:-6] or 'text'
    else:
      option_desc = None
      option_type = N_('text')
      
    # See "IniEditorBasicSecurityManager" for why we use a pipe char here.
    if ('%s|%s' % (section_name, option_name)) in self.password_options_set:
      option_type = N_('password')
      
    if section_default_values:
      default_value = (self._convert_value(section_default_values.get(option_name), option) or '')
    else:
      default_value = ''
      
    return { 'default_value': default_value, 'desc': option_desc, 'type': option_type, 
             'option_info': option, 'access': self._check_option_access(section_name, option_name) }

  def _create_new_field_instance(self, req, section_name, option_name, section_default_values, value = None):    
    option = self._gather_option_data(req, section_name, option_name, section_default_values)
    option['stored_value'] = option['default_value']
   
    self._set_option_value(req, section_name, option_name, option, value)
    return option

  def _set_option_value(self, req, section_name, option_name, option, value):
    if option['access'] != ACCESS_MODIFIABLE:
      option['value'] = option['stored_value']
      return
      
    if value is None:
      value = option['default_value']
    
    option['value'] = value
    if value != option['stored_value']:
      self._set_session_value(req, section_name, option_name, value)
    else:
      self._remove_session_value(req, section_name, option_name)
      
  def _check_option_access(self, section_name, option_name):
    return self.security_manager.get_option_access(section_name, option_name)
    
  def _is_option_value_valid(self, section_name, option_name, option_value):
    is_valid, reason = self.security_manager.is_value_valid(section_name, option_name, option_value)
    if not is_valid and (reason is None or reason == ''):
      reason = 'None specified'
    return is_valid, reason

  def _apply_section_changes(self, req, section_name, options):
    values_applied = False #indicates whether at least one value has been set
    
    for option_name, option in options.items():
      if option['access'] != ACCESS_MODIFIABLE:
        # Simply ignore options we don't have access to.
        self._remove_session_value(req, section_name, option_name) # remove if exists
        continue
      
      if option['value'] == option['default_value']:
        #
        # The option shall use its default value
        #
        if self.config.has_option(section_name, option_name):
          is_valid, reason = self._is_option_value_valid(section_name, option_name, option['default_value'])
          if not is_valid:
            add_warning(req, _('The default value for option "%s" in section "%s" is invalid. Reason: %s') % (option_name, section_name, reason))
            continue

          self.log.info("Removing option: [" + section_name + "] " + option_name)
          self.config.remove(section_name, option_name)
          
          # Check whether the option was actually removed (i.e. reset to its 
          # default value). The option can't be removed if it's set in a parent
          # trac.ini. In this case we set the default value explicitly.
          #
          # NOTE: The option may haven been defined with its default value in a
          #   parent trac.ini as well as in the project's trac ini with a 
          #   non-default value. Because of this we need to recheck against the
          #   default value here.
          if self.config.has_option(section_name, option_name) and \
             self.config.get(section_name, option_name) != option['default_value']:
            self.log.info("Removing options failed. Option may be inherited. Settings default value explicitly: " + str(option['default_value']))
            self.config.set(section_name, option_name, option['default_value'])
      else:
        #
        # The option shall use the specified value
        #
        if option['value'] != option['stored_value']:
          if option['type'] == 'password' and option['value'] == '':
            # An empty password field means: Don't change the password
            continue
          
          is_valid, reason = self._is_option_value_valid(section_name, option_name, option['value'])
          if not is_valid:
            add_warning(req, _('The value for option "%s" in section "%s" is invalid. Reason: %s') % (option_name, section_name, reason))
            continue
          
          self.log.info("Setting option: [" + section_name + "] " + option_name + " to: " + option['value'])
          self.config.set(section_name, option_name, option['value'])
          
      option['stored_value'] = option['value']
      
      # Remove applied value 
      self._remove_session_value(req, section_name, option_name)
      
      values_applied = True
      
    return values_applied
          
          
  def _discard_section_changes(self, req, section_name, options):
    for option_name, option in options.items():
      option['value'] = option['stored_value']
      self._remove_session_value(req, section_name, option_name)
      self._remove_session_custom_option(req, section_name, option_name)

  #
  # ITemplateProvider methods
  #
  def get_templates_dirs(self):
    """Return a list of directories containing the provided template files.
    """  
    from pkg_resources import resource_filename
    return [ resource_filename(__name__, 'templates') ]
    # return []

  def get_htdocs_dirs(self):
    """ Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
      
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
    """
    from pkg_resources import resource_filename
    return [('inieditorpanel', resource_filename(__name__, 'htdocs'))]
