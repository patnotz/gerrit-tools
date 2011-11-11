#!/usr/bin/env python
import argparse
import subprocess

def delete_project_sql(project):
  # Build the SQL statement.
  sql = """\
DELETE FROM ref_rights WHERE project_name = '%(project)s';
DELETE FROM account_patch_reviews WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM change_messages WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM patch_comments WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM patch_set_ancestors WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM patch_set_approvals WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM patch_sets WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM starred_changes WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM tracking_ids WHERE change_id IN (
    SELECT change_id FROM changes WHERE dest_project_name = '%(project)s');
DELETE FROM changes WHERE dest_project_name = '%(project)s';
DELETE FROM account_project_watches WHERE project_name = '%(project)s';

UPDATE projects SET parent_name = (
    SELECT parent_name FROM projects WHERE name = '%(project)s')
  WHERE parent_name = '%(project)s';
DELETE FROM projects WHERE name = '%(project)s'"""
  sql %= {'project': project}
  return sql
    
if __name__ == "__main__":

    defaultServer = "sierra-trac.sandia.gov"
    defaultPort = 5915 #29418

    parser = argparse.ArgumentParser(description='Probe Gerrit.')
    parser.add_argument('-s', '--server', metavar='SERVER', default=defaultServer, help='Gerrit server name')
    parser.add_argument('-p', '--port', metavar='PORT', type=int, default=defaultPort, help='Gerrit SSH port')
    parser.add_argument('project', metavar='PROJECT', nargs=1, help="Gerrit project to delete")
    args = parser.parse_args()

    print "Deleting project %s:%s/%s" % (args.server, args.port, args.project[0])

    sql = delete_project_sql(args.project[0])
    
    cmd = 'gerrit gsql -c "%s"' % sql
    gcmd = ["ssh", "-p", '%s' % args.port, args.server, cmd]
    response = subprocess.call(gcmd)
    print response
