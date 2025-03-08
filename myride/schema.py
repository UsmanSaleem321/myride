import graphene
import graphql_jwt
from users.schema import UserQuery, UserMutation
from rides.schema import RideQuery, RideMutation

class Query(UserQuery, RideQuery, graphene.ObjectType):
    pass

class Mutation(UserMutation, RideMutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
