import re
import httpx
import motor.motor_asyncio

TWITCH_CLIENT_ID = 'twitch Client ID'

class TwitchCommand():
    def extract_twitch_username(self,link):
        pattern = r'twitch.tv/([\w]+)'
        match = re.search(pattern, link)
        if match:
            return match.group(1)
        return None

    async def get_stream_status(self, username):
        headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': f'Bearer value'
        }
        data = httpx.get(f'https://api.twitch.tv/helix/streams?user_login={username}', headers=headers).json()
        return len(data['data']) > 0,data['data']

    async def get_is_channel(self,channel_name):
        base_url = "https://api.twitch.tv/helix/users"
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            'Authorization': f'Bearer value'
        }
        params = {
            "login": channel_name
        }
        response = httpx.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return True,data
            else:
                return False,data
        else:
            print("API 요청 중 오류 발생:", response)
            return False

class MongoDBConn:
    def __init__(self):
        self.connection_string = 'db'
        self.database = "twitch"
        self.client = None
        self.db = None

    async def __aenter__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
        self.db = self.client[self.database]
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    async def connect(self):
        if not self.client:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database]
        return self.db

    async def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
