import trac
import time
import traceback
import issue as im

count = 0
for issue in trac.issues('trac.db'):
    count = count + 1
    if issue.trac.id != count:
        values = {'id': count, 'owner': 'cash', 'summary': 'spammer ticket for import from Trac', 'description': 'This is a fake ticket to replace missing ticket in Trac', 'resolution': 'invalid', 'status': 'closed', 'component': 'Core', 'time': 1213265879, 'reporter': 'cash', 'version': 'none', '_changes_and_attachments': [], 'priority': 'low', 'milestone': None}
        fake_issue = im.issue(**values)
        fake_issue.githubify()
        fake_issue.push()
        print "PUSHED fake ticket", count
        count = count + 1
    #if issue.trac.id < 1400:
    #    continue
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

