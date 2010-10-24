#!/usr/bin/env python
import argparse
from subprocess import check_output
import json
import os.path
import sys
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

def die(message):
    print message
    sys.exit(1)

class Gerrit(object):

    def __init__(self, server, port, repo, project):
        self.__server = server
        self.__port = port
        self.__repo = repo
        self.__project = project
        self.__load()
        self.__patchset_revision_cache = {}
        nc = len(self.table('changes'))
        print "%s:%s/%s -- %d changes" % (server, port, project, nc)

    def __load(self):
        print 'Querying Gerrit...'
        table_names = []
        table_names.append('accounts')
        table_names.append('patch_sets')
        table_names.append('patch_set_ancestors')
        self.__tables = {}
        for table_name in table_names:
            cmd = 'gerrit gsql --format=JSON -c "select * from %s"' % table_name
            self.__tables[table_name] = self.json(cmd)

        cmd = 'gerrit gsql --format=JSON -c "select * from changes where dest_project_name=\'%s\' and open=\'Y\'"' % self.__project
        c = self.json(cmd)
        c.sort(cmp=lambda x, y: cmp(x['change_id'], y['change_id']))
        self.__tables['changes'] = c
            
    def table(self, name):
        return self.__tables.get(name, {})

    def json(self, cmd):
        gcmd = ["ssh", "-p", '%s' % self.__port, self.__server, cmd]
        json_txt = StringIO(check_output(gcmd))
        result = []
        for line in json_txt.readlines():
            blob = json.loads(line.strip())
            # filter out extra JSON data
            if blob.get('type') == 'row':
                result.append( blob['columns'] )
            elif blob.get('type') not in ['stats', 'query-stats']:
                result.append( blob )
        return result

    def get_revision_for_change(self, change_id, patch_id):
        # Check the local cache first
        key = (change_id, patch_id)
        rev = self.__patchset_revision_cache.get(key)
        if rev:
            return rev
        # look it up, caching records on the way
        patch_sets = self.table('patch_sets')
        for rec in patch_sets:
            this_change_id = rec['change_id']
            this_patch_id = rec['patch_set_id']
            this_key = (this_change_id, this_patch_id)
            this_rev = rec['revision']
            self.__patchset_revision_cache[this_key] = this_rev
            if this_key == key:
                return this_rev
        die("Can't find revision for change (%s, %s)" % key)
            
    def get_changes_by_topic(self):
        result = {}
        changes = self.table('changes')
        for rec in changes:
            topic = rec.get('topic')
            change_id = rec['change_id']
            account_id = rec['owner_account_id']
            user = gerrit.get_username_from_account_id(account_id)
            if topic:
                topic = '%s/%s' % (user, topic)
            else:
                topic = '%s/%s' % (user, change_id)
            result.setdefault(topic, []).append(rec)
        return result

    def get_add_delete_line_count(self, ref):
        cmd = ["git", "--git-dir=%s"%self.__repo, "diff-tree", "-w", "--numstat", ref, "%s^"%ref]
        output = StringIO(check_output(cmd))
        (adds, dels) = (0, 0)
        for line in output.readlines():
            (a, d, f) = line.split()
            adds += int(a)
            dels += int(d)
        return (adds, dels)

    def get_username_from_account_id(self, account_id):
        accounts = self.table('accounts')
        for rec in accounts:
            if rec['account_id'] == account_id:
                email = rec['preferred_email']
                return email[:email.find('@')]
    
if __name__ == "__main__":

    try:
        projectPath = check_output('git rev-parse --show-toplevel'.split(), ).strip()
        #stderr=subprocess.STDOUT
    except:
        print 'gerrit.py must be run in a git project'
        sys.exit(1)

    defaultProject = os.path.basename(projectPath)
    defaultServer = "sierra-trac.sandia.gov"
    defaultPort = 5915 #29418

    parser = argparse.ArgumentParser(description='Probe Gerrit.')
    parser.add_argument('-s', '--server', metavar='SERVER', default=defaultServer, help='Gerrit server name')
    parser.add_argument('-p', '--port', metavar='PORT', type=int, default=defaultPort, help='Gerrit SSH port')
    parser.add_argument('-r', '--project', metavar='PROJ', default=defaultProject, help='Gerrit project')

    args = parser.parse_args()

    gerrit = Gerrit(args.server, args.port, projectPath, args.project)
    changes = gerrit.table('changes')
    patch_sets = gerrit.table('patch_sets')

    print 
    print "List All Changes"
    print 
    for rec in changes:
        change_id = rec['change_id']
        patch_set_id = rec['current_patch_set_id']
        subject = rec['subject']
        topic = rec.get('topic', None)
        if topic:
            topic = '(%s)' % topic
        else:
            topic = ''
        revision = gerrit.get_revision_for_change(change_id, patch_set_id)
        print "  %s - %s %s... \"%s\"" % (change_id, topic, revision[:6], subject)

    print 
    print "List Changes by Topic"
    print 
    by_topic = gerrit.get_changes_by_topic()
    has_topicless_changes = False
    for (topic, changes) in by_topic.items():
        if topic == None: continue
        print 'topic: %s' % topic
        for rec in changes:
            change_id = rec['change_id']
            patch_set_id = rec['current_patch_set_id']
            subject = rec['subject']
            revision = gerrit.get_revision_for_change(change_id, patch_set_id)
            print "  %s - %s... \"%s\"" % (change_id, revision[:6], subject)
    changes = by_topic.get(None, [])
    for rec in changes:
        change_id = rec['change_id']
        patch_set_id = rec['current_patch_set_id']
        subject = rec['subject']
        revision = gerrit.get_revision_for_change(change_id, patch_set_id)
        print "%s - %s... \"%s\"" % (change_id, revision[:6], subject)
    
