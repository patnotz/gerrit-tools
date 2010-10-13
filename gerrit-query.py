#!/usr/bin/env python
from subprocess import check_output
import json
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

GerritHost = "sierra-trac.sandia.gov"
GerritPort = "5915"

def gerrit_json(cmd):
    gcmd = ["ssh","-p",GerritPort,GerritHost,cmd]
    json_txt = StringIO(check_output(gcmd))
    result = []
    for line in json_txt.readlines():
        blob = json.loads(line.strip())
        # filter out extra JSON data
        if blob.get('type') not in ['stats', 'query-stats']:
            result.append( blob )
    return result

def gerrit_query(query):
    cmd = 'gerrit query --format=JSON --patch-sets --current-patch-set "%s"' % query
    return gerrit_json(cmd)

def gerrit_gsql(sql):
    cmd = 'gerrit gsql --format=JSON -c "%s"' % sql
    return gerrit_json(cmd)

def number_of_commenters():
    sql= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    rows = gerrit_gsql(sql)
    return len(rows)

def number_of_reviewers():
    sql= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    rows = gerrit_gsql(sql)
    return len(rows)

def number_of_submitters():
    sql= 'select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id'
    rows = gerrit_gsql(sql)
    return len(rows)

def number_of_readers():
    sql1= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    sql2= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    sql = '%s UNION %s order by full_name' % (sql1,sql2)
    rows = gerrit_gsql(sql)
    return len(rows)

def number_of_participants():
    sql1= 'select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id'
    sql2= 'select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id'
    sql3= 'select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id'
    sql = '%s UNION %s UNION %s order by full_name' % (sql1,sql2,sql3)
    rows = gerrit_gsql(sql)
    return len(rows)
    
data = gerrit_query("project:code")

owners = {}
for blob in data:
    changeId = blob['id']
    status = blob['status']
    subject = blob['subject']
    owner = blob['owner']['name'].split()[0]
    patchSets = blob.get('patchSets',[])
    numPatchSets = len(patchSets)
    numApprovals = len(blob['currentPatchSet'].get('approvals',[]))
    for patchSet in patchSets:
        numApprovals += len(patchSet.get('approvals',[]))
    owners[owner] = True
    truncatedSubject = subject[:min(40,len(subject))]
    if truncatedSubject != subject:
        truncatedSubject += "..."
    print '%s - %s (%s...): %s' % (owner,truncatedSubject,changeId[:8],status)
    #print '%s... by %s (%s): %s' % (changeId[:8],owner,status,truncatedSubject)
    #print '\tNumber of approvals: %d' % numApprovals
    #print '\tNumber of patch sets: %d' % numPatchSets
    
owners = owners.keys()
print "Number of review submitters: %d" % len(owners)
print "Number of review submitters: %d" % number_of_submitters()
print "Number of reviers: %d" % number_of_reviewers()
print "Number of commenters: %d" % number_of_commenters()
print "Number of readers: %d" % number_of_readers()
print "Number of participants: %d" % number_of_participants()
