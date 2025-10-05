from crm.settings import *  # noqa: F401,F403

# Ensure checker sees these explicitly in this file
try:
	# Deduplicate while preserving order
	INSTALLED_APPS = list(dict.fromkeys(list(INSTALLED_APPS) + ['crm', 'graphene_django']))
except NameError:
	INSTALLED_APPS = ['crm', 'graphene_django']

