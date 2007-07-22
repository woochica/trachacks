
def validate_acl(req, acl):
    if not acl:
        return True
    components = acl.split(',')
    for aci in components:
        aci = aci.strip()
        if req.authname == aci or req.perm.has_permission(aci):
            return True
    return False

