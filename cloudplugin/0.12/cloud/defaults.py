# Default droplet config options that can be overridden in the trac.ini file.

droplet_defaults = {
  'cloud.instance': {
    'class': 'Ec2Instance', # must exactly match corresponding Python class name
    'description': 'AWS EC2 instances.',
    'title': 'EC2 Instances',
    'label': 'EC2 Instance',
    'order': 1, # order in contextual nav from left to right
    'id_field': 'name',
    'notify_jabber': '',
    
    # field definitions
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.name.handler': 'NameHandler',
    'field.run_list': 'multiselect',
    'field.run_list.label': 'Roles',
    'field.run_list.databag': 'roles', # special token
    'field.run_list.handler': 'RunListHandler',
    'field.environment': 'select',
    'field.environment.label': 'Environment',
    'field.environment.databag': 'environment',
    'field.created_by': 'text',
    'field.created_by.label': 'Created By',
    'field.created_by.handler': 'AuthorHandler',
    'field.created_at': 'text',
    'field.created_at.label': 'Created At',
    'field.created_at.handler': 'EpochHandler',
    'field.ohai_time': 'text',
    'field.ohai_time.label': 'Last Check-in',
    'field.ohai_time.handler': 'AgoEpochHandler',
    'field.ec2.instance_id': 'text',
    'field.ec2.instance_id.label': 'Instance ID',
    'field.ec2.instance_type': 'text',
    'field.ec2.instance_type.label': 'Instance Type',
    'field.ec2.hostname': 'text',
    'field.ec2.hostname.label': 'Private Hostname',
    'field.ec2.public_hostname': 'text',
    'field.ec2.public_hostname.label': 'Public Hostname',
    'field.ec2.public_hostname.handler': 'SshHandler',
    'field.ec2.placement_availability_zone': 'select',
    'field.ec2.placement_availability_zone.label': 'Availability Zone',
    'field.ec2.placement_availability_zone.options': 'No preference|us-east-1a|us-east-1b|us-east-1c|us-east-1d',
    'field.ec2.ami_id': 'text',
    'field.ec2.ami_id.label': 'Image ID',
    
    # create, read, update, delete views - chef resource name and fields
    'crud_resource': 'nodes',
    'crud_view': 'name, ec2.instance_id, run_list, created_by, created_at, ohai_time, ec2.instance_type, ec2.hostname, ec2.public_hostname, ec2.placement_availability_zone, ec2.ami_id',
    'crud_new': 'run_list, created_by, created_at, ec2.instance_type, ec2.ami_id, ec2.placement_availability_zone',
    'crud_edit': 'run_list, created_by, created_at*, ec2.instance_type*, ec2.ami_id*, ec2.placement_availability_zone*',
    
    # grid view - chef search index and fields
    'grid_index': 'node',
    'grid_columns': 'name, run_list, created_by, created_at, ohai_time, ec2.instance_type, ec2.public_hostname, ec2.placement_availability_zone, ec2.ami_id',
    'grid_group': 'environment',
    'grid_sort': 'environment',
    'grid_asc': 0,
  },
  'cloud.rds': {
    'class': 'RdsInstance', # must exactly match corresponding Python class name
    'description': 'AWS RDS instances.',
    'title': 'RDS Instances',
    'label': 'RDS Instance',
    'order': 2, # order in contextual nav from left to right
    'id_field': 'id',
    'notify_jabber': '',
    
    # field definitions
    'field.id': 'text',
    'field.id.label': 'ID',
    'field.dbname': 'text',
    'field.dbname.label': 'DB Name',
    'field.created_by': 'text',
    'field.created_by.label': 'Created By',
    'field.created_by.handler': 'AuthorHandler',
    'field.created_at': 'text',
    'field.created_at.label': 'Created At',
    'field.created_at.handler': 'EpochHandler',
    'field.availability_zone': 'select',
    'field.availability_zone.label': 'Availability Zone',
    'field.availability_zone.options': 'No preference|us-east-1a|us-east-1b|us-east-1c|us-east-1d',
    'field.multi_az': 'checkbox',
    'field.multi_az.label': 'Multi-AZ',
    'field.instance_class': 'text',
    'field.instance_class.label': 'Class',
    'field.allocated_storage': 'text',
    'field.allocated_storage.label': 'Storage',
    'field.endpoint': 'text',
    'field.endpoint.label': 'Endpoint',
    'field.endpoint.handler': 'MysqlDsnHandler',
    'field.endpoint_port': 'text',
    'field.endpoint_port.label': 'Endpoint Port',
    'field.cmd_apply_now': 'checkbox',
    'field.cmd_apply_now.label': 'Apply Immediately',
    
    # create, read, update, delete views - chef resource name and fields
    'crud_resource': 'data',
    'crud_view': 'id, dbname, created_by, created_at, availability_zone, multi_az, instance_class, allocated_storage, endpoint',
    'crud_new': 'id, dbname, created_by, created_at, availability_zone, multi_az, instance_class, allocated_storage',
    'crud_edit': 'id*, dbname*, created_by, created_at*, availability_zone*, multi_az, instance_class, allocated_storage, cmd_apply_now',
    
    # grid view - chef search index and fields
    'grid_index': 'rds', # data bag name, must match droplet name
    'grid_columns': 'id, dbname, created_by, created_at, availability_zone, multi_az, instance_class, allocated_storage, endpoint',
    'grid_group': '',
    'grid_sort': 'id',
    'grid_asc': 1,
  },
  'cloud.command': {
    'class': 'Command', # must exactly match corresponding Python class name
    'description': "Commands to execute on ec2 instances by environment and role.  Commands with an ID of 'deploy' and 'audit' will be used for deployments to and audits of environments, respectively.",
    'title': 'Commands',
    'label': 'Command',
    'order': 3, # order in contextual nav from left to right
    'id_field': 'name',
    'node_ref_field': 'alias',
    'notify_jabber': '',
    
    # field definitions
    'field.name': 'text',
    'field.name.label': 'ID',
    'field.description': 'text',
    'field.description.label': 'Description',
    'field.command': 'text',
    'field.command.label': 'Command',
    'field.cmd_environments': 'multiselect',
    'field.cmd_environments.label': 'Execute in Environments',
    'field.cmd_environments.databag': 'environment',
    'field.cmd_environments.handler': 'ListHandler',
    'field.cmd_roles': 'multiselect',
    'field.cmd_roles.label': 'Execute for Roles',
    'field.cmd_roles.databag': 'roles', # special token
    'field.cmd_roles.handler': 'ListHandler',
    
    # create, read, update, delete views - chef resource name and fields
    'crud_resource': 'data',
    'crud_view': 'name, description, command, cmd_environments, cmd_roles',
    'crud_new': 'name, description, command',
    'crud_edit': 'name*, description,  command',
    
    # grid view - chef search index and fields
    'grid_index': 'command', # data bag name, must match droplet name
    'grid_columns': 'name, description',
    'grid_group': '',
    'grid_sort': 'name',
    'grid_asc': 1,
  },
  'cloud.environment': {
    'class': 'Environment', # must exactly match corresponding Python class name
    'description': 'Per-environment/profile configuration.',
    'title': 'Environments',
    'label': 'Environment',
    'order': 4, # order in contextual nav from left to right
    'id_field': 'name',
    'node_ref_field': 'alias',
    'notify_jabber': '',
    
    # field definitions
    'field.order': 'text',
    'field.order.label': 'Order',
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.value': 'text',
    'field.value.label': 'Value',
    'field.dir': 'text',
    'field.dir.label': 'Directory',
    'field.branch': 'text',
    'field.branch.label': 'Branch',
    'field.rev': 'text',
    'field.rev.label': 'Revision',
    'field.cmd_roles': 'multiselect',
    'field.cmd_roles.label': 'Deploy to/Audit Roles',
    'field.cmd_roles.databag': 'roles', # special token
    'field.cmd_roles.handler': 'ListHandler',
    
    # create, read, update, delete views - chef resource name and fields
    'crud_resource': 'data',
    'crud_view': 'order, name, value, branch, rev, last_rev_deployed, cmd_roles',
    'crud_new': 'order, name, value, branch, rev',
    'crud_edit': 'order, name, value, branch, rev',
    
    # grid view - chef search index and fields
    'grid_index': 'environment', # data bag name, must match droplet name
    'grid_columns': 'order, name, branch, rev, last_rev_deployed',
    'grid_group': '',
    'grid_sort': 'order',
    'grid_asc': 1,
  },
}
