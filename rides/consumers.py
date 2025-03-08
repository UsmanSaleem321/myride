import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RideConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "rides_updates"
        self.room_group_name = f"rides_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        ride_id =data.get("ride_id")
        status = data.get("status")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "ride_update",
                "ride_id": ride_id,
                "status": status,
            },
        )

    async def ride_update(self, event):
        await self.send(text_data=json.dumps({"ride_id": event["ride_id"], "status": event["status"]}))