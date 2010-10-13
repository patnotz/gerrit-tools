ssh -p 5915 sierra-trac.sandia.gov 'gerrit gsql --format PRETTY -c "select full_name,preferred_email from accounts"'
