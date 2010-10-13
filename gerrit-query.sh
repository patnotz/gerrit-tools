
#ssh -p 5915 sierra-trac.sandia.gov 'gerrit query --format=JSON --patch-sets --current-patch-set project:code"'

#ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format PRETTY -c "select author_id from patch_comments"'
#ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format PRETTY -c "select distinct full_name from accounts inner join patch_comments on accounts.account_id=patch_comments.author_id order by full_name"'
#ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format PRETTY -c "select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id order by full_name"'
#ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format JSON -c "select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id order by full_name"'

ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format PRETTY -c "select distinct full_name from accounts inner join change_messages on accounts.account_id=change_messages.author_id UNION select distinct full_name from accounts inner join changes on accounts.account_id=changes.owner_account_id"'


