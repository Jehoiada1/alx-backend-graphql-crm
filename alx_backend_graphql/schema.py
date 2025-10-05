import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class CRMQuery:
    pass


class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


schema = graphene.Schema(query=Query)
