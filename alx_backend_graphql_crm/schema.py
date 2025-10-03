import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(graphene.ObjectType):
    hello = graphene.String(description="Simple hello field exposed at /graphql")

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


class RootQuery(Query, CRMQuery, graphene.ObjectType):
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=RootQuery, mutation=Mutation)
