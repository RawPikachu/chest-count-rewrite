from discord.ext import commands
import discord


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(title="Commands List", color=discord.Color.gold(), description='')
        e.set_footer(text="No more status page lul.")
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)
