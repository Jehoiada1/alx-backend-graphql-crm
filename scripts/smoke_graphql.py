import os
import json
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

import django  # noqa: E402
django.setup()

from django.test import Client  # noqa: E402


def main():
    client = Client()
    payload = {"query": "{ hello }"}
    resp = client.post("/graphql", data=json.dumps(payload), content_type="application/json")
    print("Status:", resp.status_code)
    print("Body:", resp.content.decode())
    if resp.status_code != 200:
        sys.exit(1)


if __name__ == "__main__":
    main()
