# This allows "PythonAuthnHandler mod_auth_acctmgr" instead of "PythonAuthnHandler mod_auth_acctmgr.handler" 
try:
    from handler import *
except ImportError:
    pass
