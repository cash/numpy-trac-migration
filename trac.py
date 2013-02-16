import issue
import util

fields = "id,type,time,component,severity,priority,owner,reporter,cc,version,milestone,status,resolution,summary,description,keywords"

def issues(dbfile):
    c = util.cursor(dbfile)
    c.execute("SELECT id FROM ticket")
    for (id,) in c.fetchall():
        print id
        c.execute("SELECT %s FROM ticket where id=%d" % \
                             (fields, id))
        vals = c.fetchone()
        changes = issue_changes_and_attachments(id)
        yield issue.issue(**dict(zip(fields.split(","), vals) + \
                                     [('_changes_and_attachments', changes)]))

def single_issue(dbfile, id):
    c = util.cursor(dbfile)
    c.execute("SELECT %s FROM ticket where id=%d" % \
                         (fields, id))
    vals = c.fetchone()
    changes = issue_changes_and_attachments(id)
    return issue.issue(**dict(zip(fields.split(","), vals) + \
                                  [('_changes_and_attachments', changes)]))

def issue_changes_and_attachments(id):
    c = util.cursor()
    c.execute("SELECT time, author, field, oldvalue, newvalue FROM ticket_change WHERE ticket= '%s'" %  (id,))
    for vals in c.fetchall():
        yield vals
    c.execute("SELECT time, author, description, filename FROM attachment WHERE id='%s'" % (id,))
    for vals in c.fetchall():
        yield vals
