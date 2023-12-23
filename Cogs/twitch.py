import discord,datetime,asyncio
from commands.twitch import MongoDBConn
from datetime import datetime
from dateutil.parser import parse
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from discord.commands import SlashCommandGroup
from discord.ext import commands, tasks
from commands.twitch import TwitchCommand
import httpx
import re

class ChLink(discord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.link = link
        self.add_item(discord.ui.Button(label='채널 바로가기', url=f'https://twitch.tv/{self.link}', style=discord.ButtonStyle.link))

class Twitch(commands.Cog):
    TWITCH = SlashCommandGroup(name='트위치')

    def __init__(self, app):
        self.app = app
        self.TWITCH_CLIENT_ID = 'CLIENT_ID'
        self.check_stream.start()

    @tasks.loop(seconds=15)
    async def check_stream(self):
        mongo = MongoDBConn()
        conn = await mongo.connect()
        channel_ids = []
        async for doc in conn.servers.find({}):
            channel_ids.append(doc)
        if len(channel_ids) == 0:
            return
        await asyncio.gather(*(self.process_guild(guild_id) for guild_id in channel_ids))

    async def process_guild(self, guild_id):
        try:
            stream_status = await TwitchCommand.get_stream_status(self,guild_id['channel_id'])
            if stream_status[0] != True:
                return
            stream_info = stream_status[1][0]
            if guild_id['last_vid_id'] != stream_info['id']:
                guild_id['last_vid_id'] = stream_info['id']
                mongo = MongoDBConn()
                conn = await mongo.connect()
                await conn.servers.update_one({"serverid": guild_id['serverid']}, {"$set": {"last_vid_id": guild_id['last_vid_id']}}, upsert=True)
                channel = self.app.get_channel(guild_id['chid'])
                if channel is None:
                    del guild_id['chid']
                    return
                started_at = datetime.strptime(stream_info['started_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
                embed = discord.Embed(title=f'{stream_info["title"]}',description=stream_info['user_name'],color=0xd9feed)
                embed.add_field(name='시작시간',value=f'UTC {started_at}')
                embed.add_field(name='태그',value=','.join(stream_info['tags']))
                embed.add_field(name='활동',value=stream_info['game_name'])
                embed.set_image(url=f'https://static-cdn.jtvnw.net/previews-ttv/live_user_{stream_info["user_login"]}.jpg')
                if guild_id['noti_msg'].strip():
                    await channel.send(guild_id['noti_msg'])
                await channel.send(embed=embed,view=ChLink(stream_info['user_login']))
        except Exception as e:
            print(f"에러 발생 : {e}")


    @check_stream.before_loop
    async def before_check_stream(self):
        await self.app.wait_until_ready()

    @TWITCH.command(name='영상알림', description='영상 알림 기능')
    async def set_channel_id(self, ctx, 트위치아이디, 알림메시지=' '):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond('관리자만 가능합니다.',ephemeral = True)
            return
        mongo = MongoDBConn()
        conn = await mongo.connect()
        existing_channel = await conn.servers.find_one({"serverid": ctx.guild.id})
        if existing_channel:
            await ctx.respond('이미 채널이 등록되어 있습니다. `\트위치 영상알림해제`를 사용한뒤 사용해주세요.', ephemeral=True)
            return
        checkCh, data = await TwitchCommand.get_is_channel(self,트위치아이디)
        if checkCh:
            mongo = MongoDBConn()
            conn = await mongo.connect()
            await conn.servers.update_one({"serverid": ctx.guild.id}, {"$set": {"channel_id": 트위치아이디, "noti_msg": 알림메시지, "chid": ctx.channel.id, "last_vid_id": None}}, upsert=True)
            embed = discord.Embed(title='트위치 알림 설정됨',description=f'채널 ID : {트위치아이디} ',color=0xd9feed)
            embed.add_field(name='아이디',value=data['data'][0]['id'])
            embed.set_thumbnail(url=data['data'][0]['profile_image_url'])
            embed.add_field(name='알림 메시지',value=알림메시지)
            await ctx.respond(embed=embed,view=ChLink(트위치아이디))
        else:
            await ctx.respond('올바른 채널을 입력해주세요',ephemeral=True)



    @TWITCH.command(name='영상알림해제')
    async def del_channel_id(self,ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond('관리자만 가능합니다.',ephemeral = True)
            return
        mongo = MongoDBConn()
        conn = await mongo.connect()
        result = await conn.servers.delete_one({"serverid": ctx.guild.id})
        if result.deleted_count == 0:
            await ctx.respond('트위치 알림이 설정되어있지 않습니다.',ephemeral = True)
        else:
            await ctx.respond(f'알림이 해제되었습니다.',ephemeral = True)

    def cog_unload(self):
        self.check_stream.cancel()
def setup(app):
    print('트위치 로드됨')
    app.add_cog(Twitch(app))
