mailman-console 
===============
### Command-line interaction for Mailman via the Web UI

Tested on Mailman version 2.1.14 only

## Installation 
``mm.py`` depends on Apache ``requests`` and BeautifulSoup 4: 

    pip install requests beautifulsoup4

## Configuration

mailman-console will read settings from the file ~/.mm.conf.  For example: 

    [Defaults]
    password: secret
    url_template: http://lists.software-carpentry.org/admin.cgi/*s-software-carpentry.org

Check mm.py --help for a description of the options. The ``url_template`` option
is maybe the most interesting in that it allows you to set the general form of
the URLs to the mailman list pages, but specify the string ``*s`` for where the
list name should go.  Then, on the command you only need to specify the list
name, and not the entire URL, e.g.: 

    mm.py --list_name Discuss list 

The [Defaults] section is always read. You can define sections for specific
accounts and then reference them with the ``--account_name`` command-line
option.
