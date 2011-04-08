# Default droplet config options that can be overridden in the trac.ini file.

droplet_defaults = {
  'cloud.instance': {
    'class': 'Ec2Instance', # must exactly match corresponding Python class name
    'description': 'AWS EC2 instances.',
    'title': 'EC2 Instances',
    'label': 'EC2 Instance',
    'order': 1, # order in contextual nav from left to right
    'id_field': 'name',
    
    # field definitions
    'field.name': 'text',
    'field.name.label': 'Name',
    'field.name.handler': 'NameHandler',
    'field.run_list': 'multiselect',
    'field.run_list.label': 'Roles',
    'field.run_list.databag': 'roles', # special token
    'field.run_list.handler': 'RunListHandler',
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
    'grid_sort': 'created_at',
    'grid_asc': 0,
    'grid_group': 'environment',
  },
  'cloud.rds': {
    'class': 'RdsInstance', # must exactly match corresponding Python class name
    'description': 'AWS RDS instances.',
    'title': 'RDS Instances',
    'label': 'RDS Instance',
    'order': 2, # order in contextual nav from left to right
    'id_field': 'id',
    
    # field definitions
    'field.id': 'text',
    'field.id.label': 'ID',
    'field.dbname': 'text',
    'field.dbname.label': 'DB Name',
    'field.zone': 'text',
    'field.zone.label': 'Zone',
    'field.multi_az': 'checkbox',
    'field.multi_az.label': 'Multi-AZ',
    'field.class': 'text',
    'field.class.label': 'Class',
    'field.storage': 'text',
    'field.storage.label': 'Storage',
    'field.cmd_apply_now': 'checkbox',
    'field.cmd_apply_now.label': 'Apply Immediately',
    
    # create, read, update, delete views - chef resource name and fields
    'crud_resource': 'data',
    'crud_view': 'id, dbname, zone, multi_az, class, storage',
    'crud_new': 'id, dbname, zone, multi_az, class, storage',
    'crud_edit': 'id*, dbname*, zone, multi_az, class, storage, cmd_apply_now',
    
    # grid view - chef search index and fields
    'grid_index': 'rds', # data bag name, must match droplet name
    'grid_columns': 'id, dbname, zone, multi_az, class, storage',
    'grid_sort': 'id',
    'grid_asc': 1,
  },
}
