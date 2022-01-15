from discord.ext import commands
from pymongo import MongoClient
import os
import certifi
import requests
import time
from uuid import UUID

class Wynncraft(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.bot.loop.create_task(self.server_check())
        DATABASE_URL = os.environ['DATABASE_URL']
        ca = certifi.where()
        client = MongoClient(DATABASE_URL, tlsCAFile=ca)
        self.db = client.db

    async def server_check(self):

        while True:     

            res = requests.get("https://athena.wynntils.com/cache/get/serverList")
            serverlist = res.json()["servers"]

            db_players = self.db.players
            db_server_list = self.db.server_list

            for _, server in serverlist.items():

                if (time.time() - (server["firstSeen"] / 1000)) >= 300:
                    
                    uuids = requests.post("https://api.mojang.com/profiles/minecraft", json=server["players"]).json()
                    sorted_uuids = {i["name"]:str(UUID(i["id"])) for i in uuids}

                    old_chest_count = {}

                    for _, uuid in sorted_uuids.items():

                        player = requests.get(f"https://api.wynncraft.com/v2/player/{uuid}/stats").json()

                        chests_opened = player["global"]["chestsFound"]

                        if db_players.find({"uuid": uuid, "chests_opened": {"$exists": True}}):

                            old_chest_count[uuid] = db_players.find_one({"uuid": uuid})["chests_opened"]

                        db_players.replace_one({"uuid": uuid}, {"uuid": uuid, "chests_opened": chests_opened}, upsert=True)
                    
                    
                    



