var section_count = ${len(sections)};

var info_format = '${javascript_quote(_("Modified: %(mod)d | Defaults: %(def)d | Options count: %(opt)d"))}';

function load_data(cnt, stored) {
  var info_elem;
  var s;
  
{% for section_name, section in sorted([(key, value) for key, value in sections.items()], key=lambda section: section[0]) %}\

  s = new Object();

{% for option_name, option in sorted([(key, value) for key, value in modifiable_options[section_name].items() if (value.type != 'password')], key=lambda option: option[0]) %}\
  s['${javascript_quote(option_name)}'] = '${javascript_quote(option.stored_value)}';
{% end %}

  info_elem = settings_list.find('td#section-title-${section_name.replace(':','_')} .section-info');
  cnt['${section_name.replace(':','_')}'] = { 'info_elem': info_elem, 'option_count': ${len(section)}, 'defaults_count': 0, 'modified_count': 0 };
  stored['${section_name.replace(':','_')}'] = s;
{% end %}
}
