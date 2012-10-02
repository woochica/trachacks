
###############################################################################
#
# Import test
#
###############################################################################

import os
import sys
import ConfigParser

config_file = "config.ini"
template_file = "config.ini.template"

if not os.path.isfile(config_file):
    sys.exit(
        "ERROR: Test configuration file %s not found.\n"
        "Copy %s to %s and fill in the required fields."
        % (config_file, template_file, config_file)
        )

config = ConfigParser.RawConfigParser() 

try:
    rv = config.read([config_file])
except Exception,e:
    sys.exit(
            "ERROR: Could not parse configuration file %s:\n"
            "%s"
            % (config_file, e)
            )

if not len(rv):
    sys.exit(
            "ERROR: Could not parse configuration file %s. Aborting."
            % config_file
            )


###############################################################################
#
# Config access
#
###############################################################################

def get(section, param):
    try:
        return config.get(section, param)
    except Exception,e:
        sys.exit(
                "ERROR: Missing configuration [%s], %s:\n%s"
                % (section, param, e)
                )

