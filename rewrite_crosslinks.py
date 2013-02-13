import trac
import time
import traceback

count = 0
for issue in trac.issues('trac.db'):
    if issue.trac.id < 5065:
        continue
    count = count + 1
    issue.githubify()
    issue.check_crossrefs()

