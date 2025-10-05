from django.core.management.base import BaseCommand
from django.test import Client
import json


class Command(BaseCommand):
    help = "Smoke test the GraphQL hello query via Django test client"

    def handle(self, *args, **options):
        client = Client()
        payload = {"query": "{ hello }"}
        response = client.post("/graphql", data=json.dumps(payload), content_type="application/json")
        self.stdout.write(str(response.status_code))
        self.stdout.write(response.content.decode())
        if response.status_code != 200:
            raise SystemExit(1)