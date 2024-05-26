# sonoshareapp/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ConvertPlaylistConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('playlist_conversion', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('playlist_conversion', self.channel_name)

    async def conversion_progress(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
