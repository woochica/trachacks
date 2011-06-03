#!/bin/python

import sys
import json
import time
from subprocess import Popen, STDOUT, PIPE, CalledProcessError
from daemon import Daemon

class CommandError(CalledProcessError):
    def __init__(self, returncode, cmd, out):
        CalledProcessError.__init__(self, returncode, cmd)
        self.out = out.lstrip()
    def __str__(self):
        return CalledProcessError.__str__(self) + "\n%s" % self.out

class Ec2Commander(Daemon):
    """Executes commands for each node specified by environments and roles."""
    
    def __init__(self):
        steps = ['Determining instances..']
        Daemon.__init__(self, steps, "Execution Progress", can_continue=True)
        if self.launch_data['command_id'] == 'deploy':
            self.progress.title("Deployment Progress")
        elif self.launch_data['command_id'] == 'audit':
            self.progress.title("Auditing Progress")
        
    def run(self, sysexit=True):
        self.progress.description("Executing: %s" % self.attributes['command'])
        ref_field = self.launch_data['node_ref_field']
        
        # build the query
        queries = []
        envs = self.launch_data['cmd_environments']
        if not envs:
            self.progress.error("No environment(s) selected")
            sys.exit(1)
        query = '('+' OR '.join(['environment:%s' % e for e in envs])+')'
        queries.append(query)
        roles = self.launch_data['cmd_roles']
        if not roles:
            self.progress.error("No role(s) selected")
            sys.exit(1)
        query = '('+' OR '.join(['role:%s' % r for r in roles])+')'
        queries.append(query)
        q = ' AND '.join(queries) or '*:*'
        
        self.log.debug('Querying for nodes with query %s' % q)
        nodes,_ = self.chefapi.search('node', sort=ref_field, q=q)
        if len(nodes)> 0:
            self.log.debug('Generating steps for %d nodes..' % len(nodes))
            step = 0
            steps = []
            for node in nodes:
                if self.progress.is_done(step):
                    steps.append(self.progress.get()['steps'][step])
                    step += 1
                    continue
                try:
                    ref = node[ref_field]
                except KeyError:
                    ref = node.name
                steps.append("Executing for node %s" % ref)
                step += 1
            self.progress.steps(steps)
        else:
            self.progress.error("No nodes found for query '%s'" % q)
            sys.exit(1)
        
        # send starting jabber message
        if self.launch_data['command_id'] == 'deploy':
            resource = 'environment'
            msg = "%s is deploying to %d %s instance(s)" % \
                    (self.options.started_by,len(nodes),', '.join(envs))
        elif self.launch_data['command_id'] == 'audit':
            resource = 'environment'
            msg = "%s is auditing %d %s instance(s)" % \
                    (self.options.started_by,len(nodes),', '.join(envs))
        else:
            resource = 'command'
            msg = "%s is executing '%s' to %d %s instance(s)" % \
                    (self.options.started_by,self.launch_data['command_id'],
                     len(nodes),', '.join(envs))
        self._notify_jabber(msg, resource)
        
        # Execute for each instance
        step = 0
        for node in nodes:
            # check if we restarted a prior run
            if self.progress.is_done(step):
                step += 1
                continue
            self.progress.start(step)
            host = node['ec2']['public_hostname']
            
            # prepare the command
            self.attributes['host'] = host
            try:
                self.attributes['roles_on_host'] = ','.join(node['roles'])
            except KeyError:
                self.attributes['roles_on_host'] = self._extract_roles(node)
            self.attributes['keypair_pem'] = self.chefapi.keypair_pem
            cmd = self.attributes['command'] % self.attributes
            
            # execute the command
            out = self._execute(cmd).strip()
            
            # check to update step
            lastline = out.split('\n')[-1] # skips any warnings, etc.
            try:
                data = json.loads(lastline)
                if isinstance(data,list):
                    progress = self.progress.get()
                    progress['steps'][step] += ''.join(data)
                    self.progress.set(progress)
            except:
                pass
            
            self.progress.done(step)
            step += 1
        
        # send ending jabber message
        msg = "%s's %s was successfully completed" % \
                (self.options.started_by,self.launch_data['command_id'])
        self._notify_jabber(msg, resource)
        
        if sysexit:
            sys.exit(0) # success
            
    def _extract_roles(self, node):
        """Extract roles from run_list"""
        roles = []
        for role in node.run_list:
            roles.append(role[5:-1])
        return ','.join(roles)
    
    def _execute(self, cmd, attempt=1, max=5):
        retry_returncode = int(self.launch_data.get('retry_returncode',0))
        self.log.debug("Running: %s" % cmd)
        p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if retry_returncode and p.returncode==retry_returncode and attempt<max:
            self.log.debug("Retry attempt %d of %d..\n" % (attempt+1,max))
            time.sleep(10)
            self._execute(cmd, attempt+1)
        elif p.returncode != 0:
            raise CommandError(p.returncode, cmd, out)
        else:
            self.log.info("%s\nSuccessfully ran: %s" % (out,cmd))
            return out
        
    def _notify_jabber(self, msg, resource='command'):
        if self.launch_data['command_id'] not in self.options.notify_jabber:
            return
        self.notify_jabber(msg, resource)


if __name__ == "__main__":
    daemon = Ec2Commander()
    try:
        if daemon.options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "Oops.. " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            daemon.log.error(msg)
            daemon.handler.flush()
            msg = "%s's execution errored" % daemon.options.started_by
            daemon._notify_jabber(msg)
            sys.exit(1)
