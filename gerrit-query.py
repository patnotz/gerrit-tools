#!/usr/bin/env python
import argparse
import subprocess
import json
import os.path
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

class Gerrit(object):

    def __init__(self, server, port, repo):
        self.__server = server
        self.__port = port
        self.__repo = repo
        self.__load()
        np = len(self.table('projects'))
        nc = len(self.table('changes'))
        nu = len(self.table('accounts'))
        print "%s:%s -- %d projects, %d changes, %d users" % (server, port, np, nc, nu)

    def __load(self):
        table_names = []
        table_names.append('projects')
        table_names.append('accounts')
        table_names.append('changes')
        table_names.append('change_messages')
        table_names.append('patch_sets')
        table_names.append('patch_comments')
        self.__tables = {}
        for table_name in table_names:
            cmd = 'gerrit gsql --format=JSON -c "select * from %s"' % table_name
            self.__tables[table_name] = self.json(cmd)
            
    def table(self,name):
        return self.__tables.get(name,{})

    def json(self, cmd):
        gcmd = ["ssh", "-p", '%s' % self.__port, self.__server, cmd]
        json_txt = StringIO(subprocess.check_output(gcmd))
        result = []
        for line in json_txt.readlines():
            blob = json.loads(line.strip())
            # filter out extra JSON data
            if blob.get('type') == 'row':
                result.append( blob['columns'] )
            elif blob.get('type') not in ['stats', 'query-stats']:
                result.append( blob )
        return result

    def query(self, query):
        cmd = 'gerrit query --format=JSON --patch-sets --current-patch-set "%s"' % query
        return self.json(cmd)

    def gsql(self, sql):
        cmd = 'gerrit gsql --format=JSON -c "%s"' % sql
        return self.json(cmd)

    def get_add_delete_line_count(self, ref):
        cmd = ["git","--git-dir=%s"%self.__repo,"diff-tree","-w","--numstat",ref,"%s^"%ref]
        output = StringIO(subprocess.check_output(cmd))
        (adds,dels) = (0,0)
        for line in output.readlines():
            (a,d,f) = line.split()
            adds += int(a)
            dels += int(d)
        return (adds, dels)

    def get_diff_line_count(self, ref):
        cmd = ["git","--git-dir=%s"%self.__repo,"difftool","--no-prompt","-x","diff --suppress-common-lines -y -w",ref,"%s^"%ref]
        output = StringIO(subprocess.check_output(cmd).strip())
        return len(output.readlines())

class Binify(object):

    def __init__(self, bin_tops):
        self.__bin_tops = bin_tops[:]
        self.__bin_tops.sort()
        self.__counts = []
        self.__labels = []
        for top in self.__bin_tops:
            self.__labels.append('<=%s' % top)
            self.__counts.append(0)
        self.__labels.append('>%s' % self.__bin_tops[-1])
        self.__counts.append(0)

    def add(self, value):
        found = False
        i = 0
        for top in self.__bin_tops:
            if value <= top:
                self.__counts[i] += 1
                found = True
                break
            i += 1
        if not found:
            self.__counts[-1] += 1

    def csv(self):
        for item in zip(self.__labels,self.__counts):
            print "%s,%s" % item
        
def number_of_commenters(gerrit):
    sql= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    rows = gerrit.gsql(sql)
    return len(rows)

def number_of_reviewers(gerrit):
    sql= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    rows = gerrit.gsql(sql)
    return len(rows)

def number_of_submitters(gerrit):
    sql= 'select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id'
    rows = gerrit.gsql(sql)
    return len(rows)

def number_of_readers(gerrit):
    sql1= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    sql2= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    sql = '%s UNION %s order by full_name' % (sql1,sql2)
    rows = gerrit.gsql(sql)
    return len(rows)

def number_of_participants(gerrit):
    sql1= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    sql2= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    sql3= 'select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id'
    sql = '%s UNION %s UNION %s order by full_name' % (sql1,sql2,sql3)
    rows = gerrit.gsql(sql)
    return len(rows)
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Probe Gerrit.')
    parser.add_argument('-s','--server',metavar='SERVER',default='sierra-trac.sandia.gov',help='Gerrit server name')
    parser.add_argument('-p','--port',metavar='PORT',type=int,default=5915,help='Gerrit SSH port')
    parser.add_argument('-r','--repo',metavar='DIR',default=os.path.expanduser('~/workspace/code/.git'),help='Local repo with Gerrit changes')
    parser.add_argument('-x','--exclude',metavar='ID',default=[],action='append',help='Skip ID in histogram')
    args = parser.parse_args()

    gerrit = Gerrit(args.server, args.port, args.repo)

    data = [] #gerrit.query("project:code")

    for rec in data:
        changeId = rec['id']
        status = rec['status']
        subject = rec['subject']
        owner = rec['owner']['name'].split()[0]
        patchSets = rec.get('patchSets',[])
        numPatchSets = len(patchSets)
        numApprovals = len(rec['currentPatchSet'].get('approvals',[]))
        for patchSet in patchSets:
            numApprovals += len(patchSet.get('approvals',[]))
        truncatedSubject = subject[:min(40,len(subject))]
        if truncatedSubject != subject:
            truncatedSubject += "..."
        print '%s - %s (%s...): %s' % (owner,truncatedSubject,changeId[:8],status)

    #print "Number of review submitters: %d" % number_of_submitters(gerrit)
    #print "Number of reviers: %d" % number_of_reviewers(gerrit)
    #print "Number of commenters: %d" % number_of_commenters(gerrit)
    #print "Number of readers: %d" % number_of_readers(gerrit)
    #print "Number of participants: %d" % number_of_participants(gerrit)

    changes = gerrit.table('changes')
    change_id_to_project = {}
    for rec in changes:
        id = rec['change_id']
        project = rec['dest_project_name']
        change_id_to_project[id] = project
        
    patch_sets = gerrit.table('patch_sets')
    sum_adds = 0
    sum_dels = 0
    sum_difflc = 0
    count = 0
    bins = Binify([10,50,100,300,200,400])
    for rec in patch_sets:
        id  = rec['change_id']
        rev = rec['revision']
        project = change_id_to_project[id]
        if project != 'code':
            continue
        count += 1
        difflc = gerrit.get_diff_line_count(rev)
        (adds, dels) = gerrit.get_add_delete_line_count(rev)
        print '\t%s additions, %s deletions, %s difflc ( %s )' % (adds, dels, difflc, rev)
        if id not in args.exclude:
            sum_adds += adds
            sum_dels += dels
            sum_difflc += difflc
            bins.add(difflc)
    avg_adds = int( float(sum_adds) / float(count) )
    avg_dels = int( float(sum_dels) / float(count) )
    avg_difflc = int( float(sum_difflc) / float(count) )
    print 'Average: %s additions, %s deletions, %s difflc' % (avg_adds, avg_dels, avg_difflc)

    bins.csv()
