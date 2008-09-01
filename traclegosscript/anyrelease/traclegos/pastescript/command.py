from paste.script.create_distro import CreateDistroCommand

def create_distro_command(interactive=True, args=None):
    """ front-end the CreateDistro command"""
    command = CreateDistroCommand('create')
    command.verbose = 0
    command.simulate = False
    command.interactive = interactive
    command.parse_args(args or [])
    return command

