import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from graphql_jwt.decorators import login_required
from graphene_django.forms.mutation import DjangoModelFormMutation
from users.models import CustomUser
from django.contrib.auth import get_user_model
from graphql import GraphQLError
User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "role", "phone_number", "is_verified")


class UserQuery(graphene.ObjectType):
    all_users = graphene.List(UserType)

    def resolve_all_users(self, info):
        return User.objects.all()

class RegisterUser(graphene.Mutation):
    user = graphene.Field(lambda: UserType)
    success = graphene.Boolean()

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, username, email, password):
        if User.objects.filter(username=username).exists():
            raise GraphQLError("Username already taken")
        
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        return RegisterUser(user=user, success=True)

class UserMutation(graphene.ObjectType):
    register_user = RegisterUser.Field()