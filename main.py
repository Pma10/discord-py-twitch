import discord,typing
from discord.commands import Option
from discord.ext import commands    

app = commands.Bot(command_prefix='!',intents=discord.Intents.all())

COGS = [
  "tool"
]
def get_COGS() -> typing.List[str]:
    return COGS
for cog in get_COGS():
   app.load_extension(f'Cogs.{cog}')

@app.event
async def on_ready():
   print(f"{app.user}이(가) 로그인하였습니다.")

app.run('token')
