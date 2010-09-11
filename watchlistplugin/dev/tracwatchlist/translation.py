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

# Import tracs `N_` as `T_` to mark strings already translated by trac.
# Note: Later this might also be needed for `_`.
try:
    from  trac.util.translation  import  N_ as T_
    from  trac.util.translation  import   _ as t_
except:
    T_ = N_
    t_ =  _

