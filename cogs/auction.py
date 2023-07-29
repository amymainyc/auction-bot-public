import discord
import aiohttp
from discord.ext import commands, tasks
import json
from loguru import logger
import asyncio



with open('data/config.json') as d:
    config = json.load(d)



class Auction(commands.Cog):



    def __init__(self, client):
        self.client = client



    @commands.Cog.listener()
    async def on_ready(self):
        print('Auction Bot is Ready.')
        self.get_auctions.start()



    @tasks.loop(seconds=60)
    async def get_auctions(self):
        try:
            # get sample data
            sample = await self.get_ah_data(0)
            if sample["success"] is True:
                pages = sample["totalPages"]
                bins = []
                
                # sort through other auctions
                for page in range(pages):
                    data = await self.get_ah_data(page)
                    if data["success"] is True:
                        print(page)
                        data = data["auctions"]
                        for auction in data:
                            
                            # sort through bins
                            if auction["bin"]:
                                bin = {
                                    "tier": auction["tier"].lower(),
                                    "starting_bid": auction["starting_bid"],
                                    "auctioneer": auction["auctioneer"],
                                    "uuid": auction["uuid"]
                                }
                                if auction["item_name"] == "Enchanted Book":
                                    bin["name"] = auction["item_lore"]
                                else:
                                    bin["name"] = auction["item_name"]
                                    
                                bins.append(bin)
                                await self.check_item(bin)
                            
                    else:
                        logger.warning('Auction data unavailable; Cause: ' + data["cause"])
                
                    await asyncio.sleep(.1)
                
                await self.update_lowest_bins(bins)

            else:
                logger.info('Sample data unavailable; Cause: ' + sample["cause"])
                
        except Exception as e:
            logger.exception(e)
    


    async def check_item(self, bin):
        # check if uuid has been checked before
        with open("data/pastflips.txt") as f:
            past_flips = f.read().split("\n")

        if bin["uuid"] in past_flips:
            pass
        else:
            with open('data/flipdata.json', 'r') as f:
                flip_data = json.load(f)

            # check if item names match
            for name in flip_data:
                if name in bin["name"].lower():
                    # check if item tiers match
                    for tier in flip_data[name]:
                        if tier == "any" or tier in bin["tier"]:
                            # check if prices are right
                            if bin["starting_bid"] <= flip_data[name][tier] * 0.75:
                                uuid = bin["uuid"]
                                logger.info('Auction found: ' + uuid)

                                p = flip_data[name][tier] - bin["starting_bid"]
                                profit = self.price_formatter(p)
                                lowest_bin = self.price_formatter(flip_data[name][tier])
                                price = self.price_formatter(bin["starting_bid"])
                                tier = bin["tier"].capitalize()
                                
                                if p < 500000:
                                    color = 0x00ff4c
                                elif p < 5000000:
                                    color = 0xd0ff00
                                else:
                                    color = 0xff0000
                                
                                embed = discord.Embed(
                                    title='Underpriced Auction!',
                                    color=color
                                )
                                embed.add_field(
                                    name=f"`/viewauction {uuid}`", 
                                    value=f"{bin['name']}\nTier: {tier}\nPrice: {price} coins \n\nNext Lowest: {lowest_bin} coins\nPotential Profit: {profit} coins"
                                )
                                
                                with open("data/pastflips.txt", "w") as f:
                                    f.write('\n'.join(past_flips[1:]) + '\n' + bin["uuid"])

                                for channelID in config["channels"]:
                                    channel = self.client.get_channel(channelID)
                                    await channel.send(embed=embed)



    async def get_ah_data(self, page):
        async with aiohttp.ClientSession() as session:
            async with session.get(config["api_auctions"].replace('[page]', str(page)).replace('[key]', config["apikey3"])) as data:
                return await data.json()
    
    
    
    def price_formatter(self, price):
            price = str(price)
            num = ""
            for i in range(len(price)):
                if len(price[len(price) - i:]) % 3 == 0 and num != "":
                    num = "," + num
                num = price[len(price) - i - 1] + num
            return num



    async def update_lowest_bins(self, bins):
        with open('data/flipdata.json', 'r') as f:
            flip_data = json.load(f)

        # check if item names and rarities match
        for item in flip_data:
            for tier in flip_data[item]:
                lowest_bin = 0

                if tier == "any":
                    for b in bins:
                        # check item name
                        if item.lower() in b["name"].lower():
                            if lowest_bin == 0 or b["starting_bid"] < lowest_bin:
                                lowest_bin = b["starting_bid"]
                                    
                    flip_data[item][tier] = lowest_bin

                # if not looking for specific rarity
                else:
                    for b in bins:
                        if item.lower() in b["name"].lower():
                            if b["tier"] == tier:
                                if lowest_bin == 0 or b["starting_bid"] < lowest_bin:
                                    lowest_bin = b["starting_bid"]
                                    
                    flip_data[item][tier] = lowest_bin


        with open('data/flipdata.json', 'w') as f:
            json.dump(flip_data, f, indent=4)
        logger.info('Lowest BIN prices updated.')



def setup(client):
    client.add_cog(Auction(client))
