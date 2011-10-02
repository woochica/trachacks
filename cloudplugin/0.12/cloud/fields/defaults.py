# Default droplet config options that can be overridden in the trac.ini file.

droplet_defaults = {
  'cloud': {
    'aws_key': '',
    'aws_keypair': '',
    'aws_keypair_pem': '',
    'aws_secret': '',
    'aws_username': '',
    'aws_security_groups': 'default',
    'chef_base_path': '',
    'chef_boot_run_list': '',
    'chef_boot_sudo': True,
    'chef_boot_version': '',
    'jabber_channel': '',
    'jabber_password': '',
    'jabber_port': 5222,
    'jabber_server': '',
    'jabber_username': '',
    'rds_password': '',
    'rds_username': '',
  },
  'cloud.instance': {
    'class': 'Ec2Instance', # must exactly match corresponding Python class name
    'description': 'AWS Elastic Compute Cloud (EC2) instances.',
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
    'field.run_list.index': 'role',
    'field.run_list.handler': 'RunListHandler',
    'field.env': 'select',
    'field.env.label': 'Environment',
    'field.env.index': 'env',
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
    'field.cmd_volume': 'select',
    'field.cmd_volume.label': 'EBS Volume',
    'field.cmd_volume.index': 'ebs:name:id:',
    'field.cmd_device': 'select',
    'field.cmd_device.label': 'EBS Device',
    'field.cmd_device.options': '|/dev/sdf|/dev/sdg|/dev/sdh|/dev/sdi|/dev/sdj|/dev/sdk|/dev/sdl|/dev/sdm|/dev/sdn|/dev/sdo|/dev/sdp',
    'field.disable_api_termination': 'checkbox',
    'field.disable_api_termination.label': 'Disable API Termination',
    'field.disable_api_termination.handler': 'BooleanHandler',
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'nodes',
    'crud_new': 'run_list, created_by, created_at, ec2.instance_type, ec2.ami_id, ec2.placement_availability_zone, cmd_volume, cmd_device, disable_api_termination',
    'crud_edit': 'run_list, created_by, created_at*, ec2.instance_type*, ec2.ami_id*, ec2.placement_availability_zone*, disable_api_termination',
    'crud_view': 'name, ec2.instance_id, run_list, created_by, created_at, ohai_time, ec2.instance_type, ec2.hostname, ec2.public_hostname, ec2.placement_availability_zone, ec2.ami_id, disable_api_termination',
    
    # grid view - chef search index and fields
    'grid_index': 'node',
    'grid_columns': 'name, run_list, created_by, created_at, ohai_time, ec2.instance_type, ec2.public_hostname, ec2.placement_availability_zone, ec2.ami_id',
    'grid_group': 'env',
    'grid_sort': 'env',
    'grid_asc': 0,
  },
  'cloud.ebs': {
    'class': 'EbsVolume', # must exactly match corresponding Python class name
    'description': 'AWS Elastic Block Storage (EBS) volumes.',
    'title': 'EBS Volumes',
    'label': 'EBS Volume',
    'order': 2, # order in contextual nav from left to right
    'id_field': 'id',
    'notify_jabber': '',
    
    # field definitions
    'field.id': 'text',
    'field.id.label': 'ID',
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.description': 'text',
    'field.description.label': 'Description',
    'field.zone': 'select',
    'field.zone.label': 'Availability Zone',
    'field.zone.options': 'us-east-1a|us-east-1b|us-east-1c|us-east-1d',
    'field.size': 'text',
    'field.size.label': 'Size (GB)',
    'field.snapshot': 'text',
    'field.snapshot.label': 'From Snapshot',
    'field.instance_id': 'select',
    'field.instance_id.label': 'Attached to Instance',
    'field.instance_id.index': 'node:ec2.instance_id:ec2.instance_id:',
    'field.device': 'select',
    'field.device.label': 'Attached as Device',
    'field.device.options': '|/dev/sdf|/dev/sdg|/dev/sdh|/dev/sdi|/dev/sdj|/dev/sdk|/dev/sdl|/dev/sdm|/dev/sdn|/dev/sdo|/dev/sdp',
    'field.status': 'select',
    'field.status.label': 'Status',
    'field.created_by': 'text',
    'field.created_by.label': 'Created By',
    'field.created_by.handler': 'AuthorHandler',
    'field.created_at': 'text',
    'field.created_at.label': 'Created At',
    'field.created_at.handler': 'EpochHandler',
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'data',
    'crud_new': 'name, description, zone, size, snapshot, created_by, created_at',
    'crud_edit': 'id*, name, description, zone*, size*, snapshot*, status*, instance_id, device, created_by, created_at*',
    'crud_view': 'id, name, description, zone, size, snapshot, status, instance_id, device, created_by, created_at',
    
    # grid view - chef search index and fields
    'grid_index': 'ebs', # data bag name, must match droplet name
    'grid_columns': 'id, name, zone, size, status, instance_id, device, created_by, created_at',
    'grid_group': '',
    'grid_sort': 'name',
    'grid_asc': 1,
  },
  'cloud.eip': {
    'class': 'EipAddress', # must exactly match corresponding Python class name
    'description': 'AWS Elastic IP (EIP) addresses.',
    'title': 'EIP Addresses',
    'label': 'EIP Address',
    'order': 3, # order in contextual nav from left to right
    'id_field': 'id',
    'notify_jabber': '',
    
    # field definitions
    'field.id': 'text',
    'field.id.label': 'ID',
    'field.public_ip': 'text',
    'field.public_ip.label': 'Address',
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.description': 'text',
    'field.description.label': 'Description',
    'field.instance_id': 'select',
    'field.instance_id.label': 'Instance',
    'field.instance_id.index': 'node',
    'field.created_by': 'text',
    'field.created_by.label': 'Created By',
    'field.created_by.handler': 'AuthorHandler',
    'field.created_at': 'text',
    'field.created_at.label': 'Created At',
    'field.created_at.handler': 'EpochHandler',
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'data',
    'crud_new': 'name, description, instance_id, created_by, created_at',
    'crud_edit': 'public_ip*, name, description, instance_id, created_by, created_at*',
    'crud_view': 'public_ip, name, description, instance_id, created_by, created_at',
    
    # grid view - chef search index and fields
    'grid_index': 'eip', # data bag name, must match droplet name
    'grid_columns': 'id, public_ip, name, description, instance_id, created_by, created_at',
    'grid_group': '',
    'grid_sort': 'name',
    'grid_asc': 1,
  },
  'cloud.rds': {
    'class': 'RdsInstance', # must exactly match corresponding Python class name
    'description': 'AWS Relational Database System (RDS) instances.',
    'title': 'RDS Instances',
    'label': 'RDS Instance',
    'order': 4, # order in contextual nav from left to right
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
    'field.multi_az.handler': 'BooleanHandler',
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
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'data',
    'crud_new': 'id, dbname, created_by, created_at, availability_zone, multi_az, instance_class, allocated_storage',
    'crud_edit': 'id*, dbname*, created_by, created_at*, availability_zone*, multi_az, instance_class, allocated_storage, cmd_apply_now',
    'crud_view': 'id, dbname, created_by, created_at, availability_zone, multi_az, instance_class, allocated_storage, endpoint',
    
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
    'order': 5, # order in contextual nav from left to right
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
    'field.cmd_envs': 'multiselect',
    'field.cmd_envs.label': 'Execute in Environments',
    'field.cmd_envs.index': 'env',
    'field.cmd_envs.handler': 'ListHandler',
    'field.cmd_roles': 'multiselect',
    'field.cmd_roles.label': 'Execute for Roles',
    'field.cmd_roles.index': 'role',
    'field.cmd_roles.handler': 'ListHandler',
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'data',
    'crud_new': 'name, description, command',
    'crud_edit': 'name*, description,  command',
    'crud_view': 'name, description, command, cmd_envs, cmd_roles',
    
    # grid view - chef search index and fields
    'grid_index': 'command', # data bag name, must match droplet name
    'grid_columns': 'name, description',
    'grid_group': '',
    'grid_sort': 'name',
    'grid_asc': 1,
  },
  'cloud.env': {
    'class': 'Environment', # must exactly match corresponding Python class name
    'description': 'Per-environment/profile configuration.',
    'title': 'Environments',
    'label': 'Environment',
    'order': 6, # order in contextual nav from left to right
    'id_field': 'name',
    'node_ref_field': 'alias',
    'notify_jabber': '',
    
    # field definitions
    'field.order': 'text',
    'field.order.label': 'Order',
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.description': 'text',
    'field.description.label': 'Description',
    'field.branch': 'text',
    'field.branch.label': 'Branch',
    'field.rev': 'text',
    'field.rev.label': 'Revision',
    'field.cmd_roles': 'multiselect',
    'field.cmd_roles.label': 'Deploy to/Audit Roles',
    'field.cmd_roles.index': 'role',
    'field.cmd_roles.handler': 'ListHandler',
    
    # create, read, update, delete views (CRUD) - chef resource name and fields
    'crud_resource': 'data',
    'crud_new': 'order, name, description, branch, rev',
    'crud_edit': 'order, name, description, branch, rev',
    'crud_view': 'order, name, description, branch, rev, cmd_roles',
    
    # grid view - chef search index and fields
    'grid_index': 'env', # data bag name, must match droplet name
    'grid_columns': 'order, name, description, branch, rev',
    'grid_group': '',
    'grid_sort': 'order',
    'grid_asc': 1,
  },
}
