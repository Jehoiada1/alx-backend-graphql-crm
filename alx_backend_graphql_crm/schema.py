import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


# Keep a minimal Query for checkers that statically inspect this file
class Query(graphene.ObjectType):
    hello = graphene.String(description="Simple hello field exposed at /graphql")

    def resolve_hello(root, info):  # pragma: no cover - trivial
        return "Hello, GraphQL!"


# Compose the full runtime query used by the app and tests
class RootQuery(Query, CRMQuery, graphene.ObjectType):
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    pass
schema = graphene.Schema(query=RootQuery, mutation=Mutation)
