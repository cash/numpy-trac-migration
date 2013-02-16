# -*- coding: utf-8 -*-

import util
from time import strftime, gmtime
import re
import ghissues

def _t(secs):
    return strftime("%Y-%m-%d", gmtime(secs))

def indent(str, level):
    if not isinstance(str, basestring):
        return str
    if '\n' not in str:
        return str
    prefix = "\n" + ('\t' * level)
    return prefix + (prefix).join(str.split('\n'))

class base(object):
    pass

class issue(object):
    "A trac-to-github issue"

    def __init__(self, **kwargs):
        # minimal requirements
        assert "id" in kwargs
        assert "owner" in kwargs
        assert "summary" in kwargs
        assert "description" in kwargs
        self.trac = base()
        self.trac.__dict__.update(kwargs)
        self.github = base()
        self.existing_issues = None

    def __unicode__(self):
        return "Ticket\n\tTrac\n" + \
            "\n".join("\t\t%s: %s" % (k, indent(v, 3)) for k, v in \
                          self.trac.__dict__.items()) + "\n" + \
            "\tGithub\n" + \
            "\n".join("\t\t%s: %s" % (k, indent(v, 3)) for k, v in \
                          self.github.__dict__.items())

    def __str__(self):
        return unicode(self).encode('utf-8')

    def githubify(self):
        self.gh_lookup()  # sets id
        self.gh_set_title()
        self.gh_set_body()
        self.gh_set_comments()
        self.gh_set_user()
        self.gh_set_assignee()
        self.gh_set_state()
        self.gh_set_labels()
        self.gh_set_milestone()
        self.gh_set_closed_atby()

    def gh_lookup(self):
        pass

    def gh_set_title(self):
        if self.convert_component() == 'plugins':
            self.github.title = "%s: %s (Trac #%d)" % (self.get_output_component(), self.trac.summary, self.trac.id)
        else:
            self.github.title = "%s (Trac #%d)" % (self.trac.summary, self.trac.id)

    def gh_set_body(self):
        self.github.body = self.body_header() + t2g_markup(self.trac.description)

    def body_header(self):
        header = "\n".join(["_Original ticket %s " % self.trac_url() +
                          "on %s by %s, assigned to %s._" % \
                              (_t(self.trac.time),
                               util.mention_trac_user(self.trac.reporter),
                               util.mention_trac_user(self.trac.owner)),
                          "",
                          ""])
        header = header + "Elgg version: %s\n\n" % self.trac.version
        return header

    def trac_url(self):
        return "http://trac.elgg.org/ticket/" + str(self.trac.id)

    def gh_set_comments(self):
        self.github.comments = [t2g_markup(c) for c in self.get_trac_comments()]

    def get_trac_comments(self):
        sorted_events = sorted(c for c in self.trac._changes_and_attachments)
        for event in sorted_events:
            if len(event) == 5:
                time, author, field, oldvalue, newvalue = event
                if field == 'comment' and newvalue not in ['', '<change title>']:
                    header = "_%s wrote on %s_" % (util.mention_trac_user(author), _t(time))
                    body = t2g_markup(newvalue)
                    yield "\n".join([header, "", body])
                elif field == 'milestone':
                    try:
                        new_milestone = ghissues.find_milestone(newvalue).title
                    except:
                        new_milestone = "Unscheduled"
                    yield "Milestone changed to `%s` by %s on %s" % (new_milestone, util.mention_trac_user(author), _t(time))
                elif field == 'summary':
                    yield "Title changed from `%s` to `%s` by %s on %s" % (oldvalue, newvalue, util.mention_trac_user(author), _t(time))
            elif len(event) == 4:
                time, author, description, filename = event
                url = "http://trac.elgg.org/attachment/ticket/%d/%s" % (self.trac.id, filename)
                body = "Attachment added by %s on %s: [%s](%s)" % \
                    (util.mention_trac_user(author),
                     _t(time),
                     filename,
                     url)
                yield body
        # XXX - other changes

    def gh_set_user(self):
        pass  # handled by self.body_header()

    def gh_set_assignee(self):
        self.github.assignee = util.trac_user_to_github(self.trac.owner)

    def gh_set_state(self):
        self.github.state = 'closed' if self.trac.status == 'closed' else 'open'

    def gh_set_labels(self):
        labels = []
        ticket_priority = self.get_priority()
        if ticket_priority != None:
            labels.append(ticket_priority)
        ticket_type = self.get_ticket_type()
        if ticket_type != None:
            labels.append(ticket_type)
        if self.trac.component != 'component1': # Trac default
            labels.append('comp: ' + self.convert_component())
        self.github.labels = [ghissues.find_label(l) for l in labels]

    def get_priority(self):
        if self.trac.priority == 'critical':
            return 'critical'
        if self.trac.priority == 'high':
            return 'important'
        else:
            return None


    def get_ticket_type(self):
        if self.trac.resolution == 'wontfix':
            return 'wontfix'
        elif self.trac.resolution == 'worksforme':
            return 'worksforme'
        elif self.trac.resolution == 'duplicate':
            return 'duplicate'
        elif self.trac.resolution == 'invalid':
            return 'invalid'
        elif self.trac.type == 'Enhancement':
            return 'enhancement'
        elif self.trac.type == 'Feature Request':
            return 'enhancement'
        else:
            return None


    def get_output_component(self):
        return self.trac.component.lower()

    def convert_component(self):
        if self.trac.component == 'Core':
            return 'engine'
        elif self.trac.component == 'API':
            return 'engine'
        elif self.trac.component == 'JavaScript':
            return 'javascript'
        elif self.trac.component == 'Community Site':
            return 'community'
        elif self.trac.component == 'Elgg.org Site':
            return 'elgg.org'
        elif self.trac.component == 'Documentation':
            return 'docs'
        elif self.trac.component == 'UI/UX':
            return 'ui'
        elif self.trac.component == 'Installation':
            return 'install'
        elif self.trac.component == 'Plugin Repository':
            return 'plugin repo'
        else:
            return 'plugins'


    def gh_set_milestone(self):
        self.github.milestone = ghissues.find_milestone(self.trac.milestone)

    def gh_set_closed_atby(self):
        if self.github.state == 'closed':
            self.github.comments += [c for c in self.closed_atby_comments()]

    def closed_atby_comments(self):
        sorted_events = sorted(c for c in self.trac._changes_and_attachments)
        for event in sorted_events:
            if len(event) == 5:
                time, author, field, oldvalue, newvalue = event
                if field == 'resolution':
                    yield "Resolved in Trac by %s, %s: %s" % \
                        (util.mention_trac_user(author),
                         _t(time),
                         newvalue)

    def in_github(self, existing_issues={}):
        return False
        if len(existing_issues) == 0:
            repo = ghissues.gh_repo()
            for i in repo.get_issues(state='open'):
                existing_issues[i.title] = i.number
            for i in repo.get_issues(state='closed'):
                existing_issues[i.title] = i.number
            print len(existing_issues), "existing issues"
        return existing_issues.get(self.github.title, False)


    def push(self):
        repo = ghissues.gh_repo()
        github_issue = repo.create_issue(title=self.github.title,
                                         body=self.github.body,
                                         milestone=self.github.milestone,
                                         labels=self.github.labels)
        try:
            for comment in self.github.comments:
                github_issue.create_comment(comment)
        except:
            print("!!! Error in comments for ticket %s" % self.trac.id)
        finally:
            if self.github.state == "closed":
                github_issue.edit(state='closed')
            pass

    def repush_body(self):
        repo = ghissues.gh_repo()
        existing_id = self.in_github()
        print "Replacing body in", existing_id
        github_issue = repo.get_issue(self.in_github())
        github_issue.edit(body=self.github.body)

    def repush_comments(self):
        repo = ghissues.gh_repo()
        existing_id = self.in_github()
        print "Replacing comments in", existing_id
        github_issue = repo.get_issue(self.in_github())
        for comment in github_issue.get_comments():
            comment.delete()
        try:
            for comment in self.github.comments:
                github_issue.create_comment(comment)
        except:
            print("!!! Error in comments for ticket %s" % self.trac.id)
        finally:
            if self.github.state == "closed":
                github_issue.edit(state='closed')
            pass

    def check_crossrefs(self):
        def fix_ref(old_ref):
            num = int(old_ref.group(0)[1:])
            if num > 10:  # try to avoid common non-issues
                new_num = trac_id_to_github_number(num)
                if new_num:
                    return "#%d" % new_num
            return old_ref.group(0)
        def fix_line(l):
            if l.startswith('    '):
                return l  # ignore code blocks
            if l.startswith('Ticket #'):
                return l  # ignore unquoted numpy.test() output lines
            new_line = re.sub('(?<!Python .\..\.. \()#[0-9]+(?!(( 0x00)|( PyEval)|(-Ubuntu)))', fix_ref, l)
            if l != new_line:
                print "OLD", l
                print "NEW", new_line
                print ""
            return new_line
        def fix_refs(block):
            return "\n".join(fix_line(l)
                             for l in block.split('\n'))
        old_body = self.github.body
        old_comments = [c for c in self.github.comments]
        self.github.body = fix_refs(self.github.body)
        self.github.comments = [fix_refs(c) for c in self.github.comments]
        if self.github.body != old_body:
            self.repush_body()
        if self.github.comments != old_comments:
            self.repush_comments()

def t2g_inline_code(s):
    # single line code is `code`
    s = re.sub('{{{(.*?)}}}', '`\\1`', s)
    # bold is __text__
    s = re.sub("'''(.*?)'''", '__\\1__', s)
    # italic is _text_
    s = re.sub("''(.*?)''", '_\\1_', s)
    # not all git hashes are recognized as such without markup
    s = re.sub("commit:([a-f0-9]*)", '[\\1](https://github.com/Elgg/Elgg/commit/\\1)', s)
    # links [http://elgg.org/ Elgg]
    s = re.sub(r'\[([\w\.\:/\?=&!#]+)[ ]+([\w]+)\]', r'[\2](\1)', s)
    # remove @username
    s = re.sub(r'@(\w+)', r'\1', s);
    # remove #<id>
    #s = re.sub(r'#([0-9]+)', r'(Trac Ticket \1)', s);
    return s

def t2g_markup(s):
    # First replace all inline code blocks with `code`
    s = ''.join(t2g_inline_code(line) for line in s.split('\r'))
    # Then replace any multi-line blocks with indentation.
    # Note that Trac only does multiline blocks if {{{ and }}} are on lines by themselves
    in_block = False
    new_s = []
    for line in s.split('\n'):
        if not in_block and (line.strip() == '{{{'):
            in_block = True
            new_s.append("\n")
        elif in_block and (line.strip() == '}}}'):
            in_block = False
            new_s.append("\n")
        else:
            new_s.append(('    ' + line) if in_block else line)
    return '\n'.join(new_s) # .replace('@', 'atmention:')  # avoid mentioning, REMOVE before full run

def trac_id_to_github_number(tracid, issuemap={}):
    if len(issuemap) == 0:
        repo = ghissues.gh_repo()
        for i in repo.get_issues(state='open'):
            if 'Trac #' in i.title:
                tracid = int(i.title.split('#')[-1][:-1])
                issuemap[tracid] = i.number
        for i in repo.get_issues(state='closed'):
            if 'Trac #' in i.title:
                tracid = int(i.title.split('#')[-1][:-1])
                issuemap[tracid] = i.number
        print len(issuemap), "existing issues"
    return issuemap.get(tracid, False)
