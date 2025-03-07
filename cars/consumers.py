import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SyncStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Misal kita punya satu group global "sync_updates"
        await self.channel_layer.group_add("sync_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sync_updates", self.channel_name)

    # Jika kita tidak butuh kirim pesan dari client -> server,
    # kita tidak perlu override receive()

    # Method ini sesuai "type": "sync_update" di group_send
    async def sync_update(self, event):
        # event mengandung "message"
        message = event['message']
        # Kirim ke WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
