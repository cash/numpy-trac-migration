import trac
import time
import traceback

count = 0
for issue in trac.issues('trac.db'):
    print issue.trac.id
    if issue.trac.id < 4888:
        continue
    count = count + 1
    issue.githubify()
    try:
        if not issue.in_github():
            issue.push()
            print "PUSHED", issue.github.title
            time.sleep(1)
        else:
            print "EXISTS", issue.github.title
    except Exception, e:
        print "Could not push", issue.trac.id
        traceback.print_exc()
        raise

