#!/usr/bin/env python
import argparse
import subprocess

def add_project_sql(project):
  # Build the SQL statement.
  sql = """\
INSERT INTO projects
(use_contributor_agreements
 ,submit_type
 ,name)
VALUES
('N'
,'M'
,'%(project)s');
"""
  sql %= {'project': project}
  return sql
    
if __name__ == "__main__":

    defaultServer = "sierra-trac.sandia.gov"
    defaultPort = 5915 #29418

    parser = argparse.ArgumentParser(description='Probe Gerrit.')
    parser.add_argument('-s', '--server', metavar='SERVER', default=defaultServer, help='Gerrit server name')
    parser.add_argument('-p', '--port', metavar='PORT', type=int, default=defaultPort, help='Gerrit SSH port')
    parser.add_argument('project', metavar='PROJECT', nargs=1, help="Gerrit project to add")
    args = parser.parse_args()

    print "Adding project %s:%s/%s" % (args.server, args.port, args.project[0])

    sql = add_project_sql(args.project[0])
    
    cmd = 'gerrit gsql -c "%s"' % sql
    gcmd = ["ssh", "-p", '%s' % args.port, args.server, cmd]
    response = subprocess.call(gcmd)
    print response
