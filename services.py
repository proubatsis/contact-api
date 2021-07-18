import requests

from settings import DISCORD_WEBHOOK_URL


class MessengerService:
    def send_message(self, message_content):
        raise NotImplementedError()


class MessageDeliveryFailedError(Exception):
    pass


class DiscordService(MessengerService):
    def send_message(self, message_content):
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={
                "content": message_content,
            },
        )

        if response.status_code != 204:
            raise MessageDeliveryFailedError()
