import graphene
from graphene_django.types import DjangoObjectType
from .models import Ride
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class RideStatusEnum(graphene.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    ON_TRIP = "on_trip"
    COMPLETED = "completed"
    CANCELED = "canceled"
from django.conf import settings

User = settings.AUTH_USER_MODEL

class RideType(DjangoObjectType):
    class Meta:
        model = Ride
        fields = ("id", "rider", "driver", "pickup_location", "dropoff_location", "status", "requested_at", "updated_at")

class CreateRide(graphene.Mutation):
    ride = graphene.Field(RideType)

    class Arguments:
        pickup_location = graphene.String(required=True)
        dropoff_location = graphene.String(required=True)

    def mutate(self, info, pickup_location, dropoff_location):
        rider = info.context.user
        if not rider.is_authenticated:
            raise Exception("Authentication required")

        ride = Ride.objects.create(
            rider=rider,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            status="requested"
        )
        return CreateRide(ride=ride)

class UpdateRideStatus(graphene.Mutation):
    ride = graphene.Field(RideType)

    class Arguments:
        ride_id = graphene.ID(required=True)
        status = RideStatusEnum(required=True)

    def mutate(self, info, ride_id, status):
        user = info.context.user
        ride = Ride.objects.get(id=ride_id)

        if not user.is_authenticated:
            raise Exception("Authentication required")

        if ride.driver == user:
            if status.value not in ["on_trip", "completed"]:
                raise Exception("Driver can only mark ride as 'on_trip' or 'completed'")

        elif ride.rider == user:
            if status.value != "canceled":
                raise Exception("Rider can only cancel the ride")

        else:
            raise Exception("You are not authorized to update this ride")

        ride.status = status.value
        ride.save()

        # ✅ Send WebSocket Notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "rides_updates",
            {
                "type": "ride_update",
                "ride_id": str(ride.id),
                "status": ride.status,
            },
        )

        return UpdateRideStatus(ride=ride)


class AssignDriver(graphene.Mutation):
    ride = graphene.Field(RideType)

    class Arguments:
        ride_id = graphene.ID(required=True)
        driver_id = graphene.ID(required=True)

    def mutate(self, info, ride_id, driver_id):
        ride = Ride.objects.get(id=ride_id)
        driver = User.objects.get(id=driver_id)

        if not driver.is_seller:  # Assuming is_seller indicates a driver
            raise Exception("User is not a driver")

        ride.driver = driver
        ride.status = "accepted"  # ✅ Match STATUS_CHOICES
        ride.save()
        return AssignDriver(ride=ride)

class CancelRide(graphene.Mutation):
    ride = graphene.Field(RideType)

    class Arguments:
        ride_id = graphene.ID(required=True)

    def mutate(self, info, ride_id):
        ride = Ride.objects.get(id=ride_id)
        ride.status = "cancelled"
        ride.save()
        return CancelRide(ride=ride)

class RideQuery(graphene.ObjectType):
    all_rides = graphene.List(RideType)
    ride_by_id = graphene.Field(RideType, ride_id=graphene.ID(required=True))
    rides_by_status = graphene.List(RideType, status=graphene.String(required=True))
    
    def resolve_all_rides(self, info):
        return Ride.objects.all()
    
    def resolve_ride_by_id(self, info, ride_id):
        return Ride.objects.get(id=ride_id)
    
    def resolve_rides_by_status(self, info, status):
        return Ride.objects.filter(status=status)

class RideMutation(graphene.ObjectType):
    create_ride = CreateRide.Field()
    update_ride_status = UpdateRideStatus.Field()
    assign_driver = AssignDriver.Field()
    cancel_ride = CancelRide.Field()