import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django

django.setup()

try:
    from alx_backend_graphql_crm.schema import schema
except Exception:
    from schema import schema

query = '{ hello }'
res = schema.execute(query)
if res.errors:
    print('GraphQL errors:', res.errors)
    raise SystemExit(1)
if not res.data or res.data.get('hello') != 'Hello, GraphQL!':
    print('Unexpected response:', res.data)
    raise SystemExit(2)
print('Hello smoke OK:', res.data)
