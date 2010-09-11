# Import translation functions. Fallbacks are provided for Trac 0.11.
try:
    from  trac.util.translation  import  domain_functions
    add_domain, _, N_, tag_, gettext = \
        domain_functions('watchlist', ('add_domain', '_', 'N_', 'tag_', 'gettext'))
except ImportError:
    from  trac.util.translation  import  gettext
    _, N_, tag_  = gettext, gettext, tag
    def add_domain(a,b,c=None):
        pass

