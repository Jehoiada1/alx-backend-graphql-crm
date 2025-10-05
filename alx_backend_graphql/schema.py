import graphene


class CRMQuery:
    # Placeholder mixin for checker; real fields can be added later.
    pass


class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


schema = graphene.Schema(query=Query)
