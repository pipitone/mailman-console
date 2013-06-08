#!/usr/bin/env python
import requests
import bs4
import urllib
import argparse
import ConfigParser
import os.path

DEFAULT_SECTION = "Defaults"  # Name of defaults section in config file.
                              # This section gets explicitly loaded always,
                              # unlike the ConfigParser's DEFAULT section which
                              # only supplies default values to be used in other
                              # sections. 

def main():
  """Main driver."""
  # argparse/ConfigParse integration approach via: 
  # http://blog.vwelch.com/2011/04/combining-configparser-and-argparse.html
  conf_parser = argparse.ArgumentParser(add_help = False)
  conf_parser.add_argument("-c", "--conf_file", 
      help = "Specify config file (defaults to ~/.mm.conf)", metavar="FILE")
  conf_parser.add_argument("-a", "--account_name", 
      help = "Account name (settings loaded from config file section similarly named)")
  args, remaining_argv = conf_parser.parse_known_args()
  defaults = load_config(args.conf_file, args.account_name) 
  
  parser = argparse.ArgumentParser(
      parents = [conf_parser],
      description = "Interact with the Mailman web UI")
  parser.set_defaults(**defaults)
  parser.add_argument('command', choices=['list', 'add', 'remove'], help="command")
  parser.add_argument('email', help='email address', nargs='*')
  parser.add_argument('-u', '--url',
      help = "base url to mailman instances. e.g. %s" % 
      'http://lists.example.org/admin.cgi/examplelist')
  parser.add_argument('--url_template',
      help = "templates for the base url with *s in place of list name e.g. %s" % 
      'http://lists.example.org/admin.cgi/*s-example.org')
  parser.add_argument('-l', '--list_name',
      help = "to be used in combination with --url_template")
  parser.add_argument('-p', '--password')
  args = parser.parse_args(remaining_argv)

  credentials = {"admlogin":"Let me in...", "adminpw":args.password}

  if args.url_template:  #TODO: can argparse handle these dependencies?
    assert args.url is None
    assert args.list_name
    args.url = args.url_template.replace('*s', args.list_name)

  assert args.url is not None

  # execute commands
  if 'list' in args.command:
    members = list_members(args.url, credentials)
    for e,f in members.iteritems():
      print "%s <%s>" % (f,e)

  if 'add' in args.command: 
    add_members(args.url, credentials, args.email)

  if 'remove' in args.command: 
    remove_members(args.url, credentials, args.email)

def load_config(config_file, account_name):
  if config_file:
    assert os.path.exists(config_file)  #TODO: friendly message
  else: 
    config_file = os.path.expanduser("~/.mm.conf")
    if not os.path.exists(config_file):
      return {}

  options = {}
  config = ConfigParser.SafeConfigParser()
  config.read([config_file])

  if config.has_section(DEFAULT_SECTION): 
    options.update(config.items(DEFAULT_SECTION))

  if account_name:
    assert config.has_section(account_name)
    options.update(config.items(account_name))

  return options

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
  
  def chunk_url_tag(tag):
    return tag.name == 'a' and \
           tag.has_attr('href') and \
           'chunk' in tag.attrs['href']

  list_url = url + "/members/list?letter=0"
  r = requests.post(list_url, data=credentials)
  soup = bs4.BeautifulSoup(r.text)

  # if the lists page doesn't have links to other pages, then just scrape it
  pages = [t.attrs['href'] for t in soup.find_all(page_url_tag)] or [list_url]

  # each page for a letter can, itself, be paginated into "chunks".
  # the bottom of each page has links to chunks >= 1
  members = {}
  for page in pages:
    chunk = 0
    maxchunk = 0
    while chunk <= maxchunk:
      chunk_url = page + "&chunk=" + str(chunk)
      r    = requests.post(chunk_url, data=credentials)
      soup = bs4.BeautifulSoup(r.text)
      tags = soup.find_all(fullname_tag)
      for tag in tags:
        realname = tag.attrs['value']
        email    = urllib.unquote(tag.attrs['name'][:-len('_realname')])
        members[email] = realname

      chunk += 1
      chunks = soup.find_all(chunk_url_tag)
      maxchunk = max([int(c.attrs['href'].split("=")[-1]) for c in chunks]+[0])
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

def print_messages(r): 
  """Print any messages returned by mailman after an operation"""
  soup = bs4.BeautifulSoup(r.text)
  messages = soup.body.findChildren('h5')
  for message in messages:
    print message.get_text()
    ul = message.find_next_sibling('ul')
    if ul: 
      print ul.get_text()

if __name__ == '__main__':
  main()
