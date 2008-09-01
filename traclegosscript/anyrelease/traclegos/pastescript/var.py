# XXX consolidate pastescript vars with trac options

def vars2dict(_dict, *vars):
    if _dict is None:
        _dict = {}
    for var in vars:
        _dict[var.name] = var
    return _dict

def dict2vars(_dict):
    return [ _dict[key] for key in sorted(_dict.keys()) ]
