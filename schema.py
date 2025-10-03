"""Compatibility schema at project root for checkers importing 'schema.schema'."""

import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
	pass


class Mutation(CRMMutation, graphene.ObjectType):
	pass


schema = graphene.Schema(query=Query, mutation=Mutation)


