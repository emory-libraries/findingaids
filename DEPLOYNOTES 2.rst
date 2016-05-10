---
layout: post
title: Setup Finding Aids
---

# Setup Finding Aids

Install Python first:
> brew install python

Reference:
[Installing pip on Mac OS X](http://stackoverflow.com/questions/17271319/installing-pip-on-mac-os-x)

You can install it through Homebrew on OS X. But why should you install Python with Homebrew?

> The version of Python that ships with OS X is great for learning but it’s not good for development. The version shipped with OS X may be out of date from the official current Python release, which is considered the stable production version. (source)

> Homebrew is something of a package manager for OS X. Find more details on the Homebrew page. Once Homebrew is installed, run the following to install the latest Python, Pip & Setuptools:

> `brew install python`

Reference:
[Python, Pip on Mac OS X Yosemite] (http://www.lecloud.net/post/119427148455/python-pip-on-mac-os-x-yosemite)

Once you finish the installation and have an environment created, you can proceed to the next step which is to check out the repository and 'bundle' with:

`pip install -r pip-install-req.txt`

Subversion can be installed via brew:
`brew install subversion`

Celery and RabbitMQ can be installed with brew as well:
`brew install rabbitmq`

Reference:
[How to install Celery on Django and Create a Periodic Task](http://www.marinamele.com/2014/02/how-to-install-celery-on-django-and.html)

To verify that Rabbit is running we can try:
`sudo rabbitmq-server -detached`

Where the `-detached` flag indicates the server to run in the background. To stop the server use `manage.py migrate`

To stop the RabbitMQ service we can use:
`sudo rabbitmqctl stop`

FOB can also be installed via brew:
`brew install fob`

If the app is installed correctly we can create a superuser with:
`./manage.py createsuperuser`

> emory_ldap.EmoryLDAPUser: (emory_ldap.W101) EmoryLDAPUser has been deprecated as of Django 1.7. This model should *only* be used for migrating user information to auth.User or a local User model.
> HINT: Use django-auth-ldap for LDAP login functionality
> Username (leave blank to use 'yli60'): yang
> Email address:
> Password:
> Password (again):
> Superuser created successfully.

If you can see above information then it means you have created a superuser most likely.

Another tip is that you should make sure that you are always using your virtualenvironment while working on a specific Django project:
> (finding-aids)wml-yli60:findingaids yli60$

Show migration status:
> ./manage.py showmigrations

We can also visit the Django admin page by going to:
> http://localhost:8000/db-admin/

We might also need some fixture data (dummy/sample data) so that the site will actually render some contents. I received some json files from Rebecca.

> dev_archives.json
> dev_archivists.json
> dev_users.json

When I was installing the Finding Aids I did run into an error that is related to eullocal library/module. And here are some attempts to fix:

`pip install -r pip-install-req.txt`

if it doesn’t update the `eullocal`, you may have to run

`pip uninstall eullocal`

In order to load data (fixture from a json file) we can use the `loaddata` function as:
`manage.py loaddata`

Reference:
[loaddata](https://docs.djangoproject.com/en/1.9/ref/django-admin/#loaddata)

> django.db.utils.OperationalError: Problem installing fixture '/Users/yli60/Documents/emory/repos/findingaids/./data/dev_archives.json': Could not load fa.Archive(pk=1): no such table: taskresult_taskresult


looks like i have a missing table? migration related might be?
We'd like to use the latest Django version post the upgrade

`pip install -U Django`
`pip freeze | grep loc`

Reference:
[How to check Django version](http://stackoverflow.com/questions/6468397/how-to-check-django-version)


My problem turns out to be I installed packages outside the virtualenvironment. So the take home message is to make sure that you installed packages via pip **inside** your virtualenv

System check identified 1 issue (0 silenced).

> You have unapplied migrations; your app may not work properly until they are applied.
> Run 'python manage.py migrate' to apply them.

Then we can try `python manage.py createsuperuser` again
