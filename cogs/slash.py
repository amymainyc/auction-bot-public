from discord.ext import commands
import discord
import aiohttp
import json
from loguru import logger
import base64



with open('data/config.json') as d:
    config = json.load(d)



class Slash(commands.Cog):



    def __init__(self, bot):
        self.bot = bot
        
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    @discord.slash_command(
        name="ping",
        description="pings the bot",
        guild_ids=config["guilds"]
    )
    async def ping(self, ctx):
        await ctx.respond(f"Pong!")

    @discord.slash_command(
        name="add_item",
        description="adds an item for the auction bot to check",
        guild_ids=config["guilds"]
    )
    async def add_item(
        self, 
        ctx, 
        item_name:str, 
        rarity: discord.Option(
            str, 
            description="the item's rarity", 
            choices=[
                "any",
                "common",
                "uncommon",
                "rare",
                "epic",
                "legendary",
                "mythic",
                "special"
            ]
        )
    ):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond('```You do not have permission to use this command.```')
        
        with open("data/flipdata.json") as f:
            flip_data = json.load(f)
        if not item_name in flip_data:
            flip_data[item_name] = {}    
        flip_data[item_name][rarity] = 0
        with open("data/flipdata.json", "w") as f:
            json.dump(flip_data, f, indent=4)
        self.push_to_github()
            
        await ctx.respond(f"```Item added: {item_name}, {rarity}```")
        


    async def push_to_github(self):
        logger.info('Pushing files to Github...')
        filenames = ["data/flipdata.json", "data/pastflips.txt"]
        for filename in filenames:
            try:
                token = config["github_oath"]
                repo = "amymainyc/auction-bot"
                branch = "main"
                url = "https://api.github.com/repos/" + repo + "/contents/" + filename

                base64content = base64.b64encode(open(filename, "rb").read())

                async with aiohttp.ClientSession() as session:
                    async with session.get(url + '?ref=' + branch, headers={"Authorization": "token " + token}) as data:
                        data = await data.json()
                sha = data['sha']

                if base64content.decode('utf-8') + "\n" != data['content']:
                    message = json.dumps(
                        {"message": "Automatic data update.",
                         "branch": branch,
                         "content": base64content.decode("utf-8"),
                         "sha": sha}
                    )

                    async with aiohttp.ClientSession() as session:
                        async with session.put(
                            url, 
                            data=message, 
                            headers={"Content-Type": "application/json", "Authorization": "token " + token}
                        ) as resp:
                            print(resp)
                else:
                    logger.info("Nothing to update.")
            except Exception as e:
                logger.exception(e)



    @discord.slash_command(
        name="push",
        description="pushes files to github (dev only)",
        guild_ids=config["guilds"],
    )
    async def push(self, ctx):
        if ctx.author.id != 430079880353546242:
            return await ctx.respond("```You do not have permission to use this command.```")
        await self.push_to_github()
        await ctx.respond("```Pushed latest files to GitHub.```")



    @discord.slash_command(
        name="reset",
        description="resets the flipdata.json file (dev only)",
        guild_ids=config["guilds"],
    )
    async def reset(self, ctx):
        with open("data/flipdata.json") as f:
            data = json.load(f)
            
        for item in data:
            for tier in data[item]:
                data[item][tier] = 0
        
        with open("data/flipdata.json", "w") as f:
            json.dump(data, f, indent=4)
        
        await ctx.respond("```Reset flipdata.json.```")
            
            
            
def setup(bot):
    bot.add_cog(Slash(bot))