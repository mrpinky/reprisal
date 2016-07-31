from discord.ext import commands
import discord
from .utils import config
from .utils import checks
import re

class Roles:
    """Class to handle management of roles on the server"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='create role', aliases=['add role'], pass_context=True)
    @checks.customPermsOrRole(manage_server=True)
    async def create_role(self, ctx):
        """This command can be used to create a new role for this server"""
        # Save a couple variables that will be used repeatedly
        author = ctx.message.author
        server = ctx.message.server
        channel = ctx.message.channel
        
        # A couple checks that will be used in the wait_for_message's
        num_separated_check = lambda m: re.search("(\d,? ?)+",m.content) is not None
        yes_no_check = lambda m: re.search("(yes|no)",m.content.lower()) is not None
        
        # No use in running through everything if the bot cannot create the role
        if not server.me.permissions_in(channel).manage_roles:
            await self.bot.say("I can't create roles in this server, do you not trust  me? :c")
            return
            
        # Start the checks for 
        await self.bot.say("Alright! I'm ready to create a new role, please respond with the name of the role you want to create")
        msg = await self.bot.wait_for_message(timeout=60.0, author=author, channel=channel)
        if msg is None:
            await self.bot.say("You took too long. I'm impatient, don't make me wait")
            return
        name = msg.content
            
        # Print a list of all the permissions available, then ask for which ones need to be active on this new role
        all_perms = [p for p in dir(discord.Permissions) if isinstance(getattr(discord.Permissions,p),property)]
        fmt = "\n".join("{}) {}".format(i,perm) for i,perm in enumerate(all_perms)))
        await self.bot.say("Sounds fancy! Here is a list of all the permissions available. Please respond with just "
                            "the numbers, seperated by commas, of the permissions you want this role to have.\n```{}```".format(fmt))
        msg = await self.bot.wait_for_message(timeout=60.0, author=author, channel=channel, check=num_separated_check)
        if msg is None:
            await self.bot.say("You took too long. I'm impatient, don't make me wait")
            return
        
        # Check if any integer's were provided that are within the length of the list of permissions
        num_permissions = [int(i) for i in re.split(' ?,?',msg) if i.isdigit() and int(i) < len(all_perms)]
        if len(num_permissions) == 0:
            await self.bot.say("You did not provide any valid numbers! Try better next time.")
            return
        
        # Check if this role should be in a separate section on the sidebard, i.e. hoisted
        await self.bot.say("Do you want this role to be in a separate section on the sidebar? (yes or no)")
        msg = await self.bot.wait_for_message(timeout=60.0, author=author, channel=channel, check=yes_no_check)
        if msg is None:
            await self.bot.say("You took too long. I'm impatient, don't make me wait")
            return
        hoist = True if msg.content.lower() == "yes" else False
        
        # Check if this role should be able to be mentioned
        await self.bot.say("Do you want this role to be mentionable? (yes or no)")
        msg = await self.bot.wait_for_message(timeout=60.0, author=author, channel=channel, check=yes_no_check)
        if msg is None:
            await self.bot.say("You took too long. I'm impatient, don't make me wait")
            return
        mentionable = True if msg.content.lower() == "yes" else False
        
        # Ready to actually create the role
        perms = discord.Permissions.none()
        for index in num_permissions:
            setattr(perms, all_perms[index], True)
        
        payload = {
        'name': name,
        'permissions': perms.value,
        'hoist': hoist,
        'mentionable': mentionable
        }
        role = await self.bot.add_role(server, payload)
        await self.bot.say("We did it! You just created the new role {}".format(role.name))
        
def setup(bot):
    bot.add_cog(Roles(bot))