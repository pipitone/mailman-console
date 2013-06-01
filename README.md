mailman-console 
===============
### Command-line interaction for Mailman via the Web UI

Tested on Mailman version 2.1.14 only

## Installation 
``mm.py`` depends on Apache ``requests`` and BeautifulSoup 4: 

    pip install requests beautifulsoup4

## Known bugs
 - ``list`` command does not search chunks (so be sure to have a large ``admin_member_chunksize`` set). 
