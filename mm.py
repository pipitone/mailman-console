#!/usr/bin/env python
import requests
import bs4
import urllib
import argparse

def print_messages(r): 
  """Print any messages returned by mailman after an operation"""
  soup = bs4.BeautifulSoup(r.text)
  messages = soup.body.findChildren('h5')
  for message in messages:
    print message.get_text()
    ul = message.find_next_sibling('ul')
    if ul: 
      print ul.get_text()

def list_members(url, credentials):
  """Fetch members of the list located at url"""
  def fullname_tag(tag):
    return tag.name == 'input' and \
           tag.has_attr('name') and \
           tag.attrs['name'].endswith('realname')

  def page_url_tag(tag): 
    return tag.name == 'a' and \
           tag.has_attr('href') and \
           tag.attrs['href'][:-1].endswith('members?letter=')

  list_url = url + "/members/list"
  r = requests.post(list_url, data=credentials)
  soup = bs4.BeautifulSoup(r.text)

  # if the lists page doesn't have links to other pages, then just scrape it
  pages = [t.attrs['href'] for t in soup.find_all(page_url_tag)] or [list_url]

  members = {}
  for page in pages:
    r = requests.post(page, data=credentials)
    soup = bs4.BeautifulSoup(r.text)
    tags = soup.find_all(fullname_tag)
    for tag in tags:
      realname = tag.attrs['value']
      email    = urllib.unquote(tag.attrs['name'][:-len('_realname')])
      members[email] = realname
  return members

def add_members(url, credentials, emails, invite = False, invitation = "", \
    welcome = False, notify_owner = False): 
  """Add a list of emails to a list"""

  payload = dict(credentials)
  payload['subscribe_or_invite'] = (invite and 1 or 0)
  payload['send_welcome_msg_to_this_batch'] = (welcome and 1 or 0)
  payload['send_notifications_to_list_owner'] = (notify_owner and 1 or 0)
  payload['subscribees'] = "\n".join(emails)
  payload['invitation'] = invitation
  payload['subscribees_upload'] = ''
  payload['setmemberopts_btn'] = "Submit Your Changes"

  r = requests.post(url + "/members/add", data=payload)
  print_messages(r)

def remove_members(url, credentials, emails, ack = False, notify_owner = False): 
  """Remove a list of emails from a list"""

  payload = dict(credentials)
  payload['send_unsub_ack_to_this_batch'] = (ack and 1 or 0)
  payload['send_unsub_notifications_to_list_owner'] = (notify_owner and 1 or 0)
  payload['unsubscribees'] = "\n".join(emails)
  payload['unsubscribees_upload'] = ''
  payload['setmemberopts_btn'] = "Submit Your Changes"

  r = requests.post(url + "/members/remove", data=payload)
  print_messages(r)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description = "Interact with the Mailman web UI")
  parser.add_argument('command', choices=['list', 'add', 'remove'], help="command")
  parser.add_argument('email', help='email address', nargs='*')
  parser.add_argument('-u', '--url', required = True,
      help = "base url to mailman instances. e.g. %s" % 
      'http://lists.example.org/admin.cgi/examplelist')
  parser.add_argument('-p', '--password', required = True)
  args = parser.parse_args()

  credentials = {"admlogin":"Let me in...", "adminpw":args.password}

  if 'list' in args.command:
    members = list_members(args.url, credentials)
    for e,f in members.iteritems():
      print "%s <%s>" % (f,e)
  if 'add' in args.command: 
    add_members(args.url, credentials, args.email)
  if 'remove' in args.command: 
    remove_members(args.url, credentials, args.email)
