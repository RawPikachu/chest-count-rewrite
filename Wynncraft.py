from discord.ext import commands
from pymongo import MongoClient
import os
import certifi
import requests
import time
from tabulate import tabulate
from dotenv import load_dotenv
from uuid import UUID

load_dotenv()

class Wynncraft(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.bot.loop.create_task(self.server_check())
        DATABASE_URL = os.environ['DATABASE_URL']
        ca = certifi.where()
        client = MongoClient(DATABASE_URL, tlsCAFile=ca)
        self.db = client.db

    @commands.command("chestcount")
    async def _chestcount(self, ctx):

        collection = self.db.server_list
        db_server_list = list(collection.find({}).sort([('$natural', 1)]))

        table = [[db_server["server"], db_server["chest_count"]] for db_server in db_server_list]
        table.insert(0, ["Server", "Chest Count (30 mins)"])

        tabulated_table = tabulate(table)

        await ctx.send(f"```prolog\n{tabulated_table}\n```")


    async def server_check(self):

        while True:     

            res = requests.get("https://athena.wynntils.com/cache/get/serverList")
            serverlist = res.json()["servers"]

            db_players = self.db.players
            db_server_list = self.db.server_list

            for server, data in serverlist.items():

                if (time.time() - (data["firstSeen"] / 1000)) >= 300:

                    chunk = lambda list: [list[i:i+10] for i in range(0, len(list), 10)]
                    name_chunks = chunk(data["players"])

                    uuid_list = []
                    for chunk in name_chunks:

                        uuid_list.append(requests.post("https://api.mojang.com/profiles/minecraft", json=chunk).json())

                    uuids = sum(uuid_list, [])

                    sorted_uuids = {i["name"]:str(UUID(i["id"])) for i in uuids}

                    old_chest_count = []
                    new_chest_count = []

                    for _, uuid in sorted_uuids.items():

                        player = requests.get(f"https://api.wynncraft.com/v2/player/{uuid}/stats").json()

                        chests_opened = player["data"][0]["global"]["chestsFound"]

                        if db_players.find_one({"uuid": uuid, "chests_opened": {"$exists": True}}):

                            old_chest_count.append(db_players.find_one({"uuid": uuid})["chests_opened"])

                        else:

                            old_chest_count.append(chests_opened)
                        
                        new_chest_count.append(chests_opened)

                        db_players.replace_one({"uuid": uuid}, {"uuid": uuid, "chests_opened": chests_opened}, upsert=True)

                    server_chest_count = sum(new_chest_count) - sum(old_chest_count)

                    db_server_list.replace_one({"server": server}, {"server": server, "chest_count": server_chest_count}, upsert=True)
                    
                    
                    



