import discord
import re
import random
import os
from dotenv import load_dotenv
from asyncio import sleep
from asyncio import create_task
from tft_data_retriever import get_recent_tft_data
from tft_data_retriever import get_patch_note_data
from tft_data_retriever import HTMLDataTuple
from tft_data_retriever import get_recent_patch_title
from guild_db_handler import GuildDataHandler
from guild_db_handler import GuildNotFoundError

TFT_PATCH_NOTES_REGEX = re.compile(
    r"^https:\/\/teamfighttactics\.leagueoflegends\.com\/[a-z-]+\/news\/game-updates\/teamfight-tactics-patch-\d{2}-\d{1,2}-notes\/?$"
)
TFT_PATCH_YEAR_NOTES_REGEX = re.compile(
    r"^https:\/\/teamfighttactics\.leagueoflegends\.com\/[a-z-]+\/news\/game-updates\/teamfight-tactics-patch-\d{2}-\d{1,2}-notes-\d{4}\/?$"
)

class TFTBotClient(discord.Client):  
    def __init__(self, intents: discord.Intents):
        super().__init__(intents=intents)
        self.commands = ['&tftrecent', '&tft','&commands','&starttftcheck','&stoptftcheck']
        self.embed_icon = 'https://play-lh.googleusercontent.com/ujcV4gcP4wyioFxcRREDoC9bDZP6t4NKjgZAvkrzpvgvBYCihWXhQLCyG0Rnqvc8lQ'
        self.guild_db = GuildDataHandler()

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        create_task(self.start_tft_check())

    async def on_guild_join(self,guild):
        self.guild_db.add_guild(guild.id)

    async def on_guild_remove(self,guild):
        self.guild_db.remove_guild(guild.id)
    
    async def guild_enable_tft_check(self,message):
        if message.guild:
            guild_id = message.guild.id
            try:
                guild_perm = self.guild_db.check_guild(guild_id)
            except GuildNotFoundError:
                self.guild_db.add_guild(guild_id)
                guild_perm = self.guild_db.check_guild(guild_id)
            if guild_perm is True:
                await message.channel.send('You already have permissions enabled!')
            else:
                self.guild_db.update_guild(guild_id,True)
                await message.channel.send('TFT Check has been enabled!')

    async def guild_disable_tft_check(self,message):
        if message.guild:
            guild_id = message.guild.id
            guild_perm = self.guild_db.check_guild(guild_id)
            if guild_perm is False:
                await message.channel.send('TFT Check has not been started ')
            else:
                self.guild_db.update_guild(guild_id,False)
                await message.channel.send('TFT Check has been disabled.')

    async def send_tft_data(self, patch_data_list, channel):
        assert all(isinstance(item, HTMLDataTuple) for item in patch_data_list)
        embed_list = []
        current_embed = discord.Embed()
        if patch_data_list[0].type == 'patch-title':
            embed_patch_title = patch_data_list[0].content
        current_embed.set_author(name=embed_patch_title, icon_url=self.embed_icon)
        current_embed.description = ""
        current_embed_len = 0
        curr_field_title = ""
        curr_field_value = ""
        msg_len = 0
        i = 0
        while i < len(patch_data_list):
            if msg_len < 4500 and len(embed_list) < 9:
                if current_embed_len < 3000:
                    if patch_data_list[i].type == "header-primary":
                        if current_embed.title is not None:
                            if len(curr_field_value) > 0:
                                current_embed.add_field(name=curr_field_title, value=curr_field_value, inline=False)
                            embed_list.append(current_embed)
                            current_embed = discord.Embed()
                            current_embed_len = 0
                            current_embed.set_author(name=embed_patch_title, icon_url=self.embed_icon)
                            current_embed.description = ""
                            current_embed_len += (len(embed_patch_title)+len(self.embed_icon))
                            msg_len += (len(embed_patch_title)+len(self.embed_icon))
                            current_embed_len += (len(embed_patch_title)+len(self.embed_icon))
                        current_embed.title=patch_data_list[i].content
                        curr_field_title = ""
                        curr_field_value = ""
                    elif patch_data_list[i].type == "change-detail-title":
                        if len(curr_field_title) == 0:
                            msg_len += len(patch_data_list[i].content)
                            current_embed_len += len(patch_data_list[i].content)
                            curr_field_title = patch_data_list[i].content
                        else:
                            current_embed.add_field(name=curr_field_title, value=curr_field_value, inline=False)
                            msg_len += len(patch_data_list[i].content)
                            current_embed_len += len(patch_data_list[i].content)
                            curr_field_title = patch_data_list[i].content
                            curr_field_value = ""
                    elif patch_data_list[i].type in {"href", "img"}:
                        current_embed.set_image(url=patch_data_list[i].content)
                        msg_len += len(patch_data_list[i].content)
                        current_embed_len += len(patch_data_list[i].content)
                        embed_list.append(current_embed)
                        current_embed = discord.Embed()
                        current_embed.set_author(name=embed_patch_title, icon_url=self.embed_icon)
                        current_embed.description = ""
                        msg_len += (len(embed_patch_title)+len(self.embed_icon))
                        current_embed_len += len(patch_data_list[i].content)
    
                    elif patch_data_list[i].type in {"blockquote", "divider", "p", "li"}:
                        if len(curr_field_title) == 0 and len(current_embed.fields) == 0:
                            msg_len += len(patch_data_list[i].content)
                            current_embed_len += len(patch_data_list[i].content)
                            current_embed.description += patch_data_list[i].content
                        else:
                            msg_len += len(patch_data_list[i].content)
                            current_embed_len += len(patch_data_list[i].content)
                            if len(curr_field_value) < 800 and (len(curr_field_value) + len(patch_data_list[i].content) < 800):
                                curr_field_value += patch_data_list[i].content
                            else:
                                if len(curr_field_value) > 1000:
                                    while len(curr_field_value) > 1000:
                                        current_embed.add_field(name=curr_field_title, value=curr_field_value[0:850], inline=False)
                                        curr_field_value = curr_field_value[850:]
                                        #current_embed.add_field(name="", value=curr_field_value[850:], inline=False)
                                    current_embed.add_field(name=curr_field_title, value=curr_field_value, inline=False)
                                    msg_len += len(patch_data_list[i].content)
                                    current_embed_len += len(patch_data_list[i].content)
                                    curr_field_title = ""
                                    curr_field_value = patch_data_list[i].content
                                else:
                                    current_embed.add_field(name=curr_field_title, value=curr_field_value, inline=False)
                                    msg_len += len(patch_data_list[i].content)
                                    current_embed_len += len(patch_data_list[i].content)
                                    curr_field_title = ""
                                    curr_field_value = patch_data_list[i].content
        
                    i +=1
                else:
                    embed_list.append(current_embed)
                    current_embed = discord.Embed()
                    current_embed.set_author(name=embed_patch_title, icon_url=self.embed_icon)
                    current_embed_len = 0
                    current_embed_len += (len(embed_patch_title)+len(self.embed_icon))
                    msg_len += (len(embed_patch_title)+len(self.embed_icon))
                    current_embed.description = ""
            else:
                await channel.send(embeds=embed_list)
                embed_list = []
                msg_len = 0
                #current_embed_len = 0
        if len(embed_list) > 0:
            await channel.send(embeds=embed_list)
        if current_embed is not None:
            await channel.send(embed=current_embed)

    async def on_message(self, message):
        if message.content == self.commands[0]:
            patch_data = await get_recent_tft_data()

            await self.send_tft_data(patch_data,message.channel)
        elif message.content.startswith(self.commands[1]): 
            tft_link = await self.check_tft_link(message.content)
            if len(tft_link) != 0:
                patch_data = await get_patch_note_data(tft_link)
                if len(patch_data) > 0:
                    total_patch_data = [HTMLDataTuple(type="patch-title", content=f'Teamfight Tactics patch {message.content[5:]} notes')]
                    total_patch_data.extend(patch_data)
                    await self.send_tft_data(total_patch_data,message.channel)
                else:
                    await message.channel.send("Failed to retrieve patch notes.")
            else:
                await message.channel.send('Sorry, that URL was invalid')
        elif message.content == self.commands[2]:
            embed = discord.Embed(title="Commands:",
                  description="&tft <number.number.year>(patch number, year is optional for duplicate patch numbers\n&tftrecent\n&starttftcheck\n&stoptftcheck",
                  colour=0x00b0f4)
            embed.set_author(name="TFT BOT",
             icon_url=self.embed_icon)
            await message.channel.send(embed=embed)
        elif message.content == self.commands[3]:
            await self.guild_enable_tft_check(message)
        elif message.content == self.commands[4]:
            await self.guild_disable_tft_check(message)
    
    async def start_tft_check(self):
        current_patch = await get_recent_patch_title()
        while True:
            new_patch = await get_recent_patch_title()
            if new_patch != current_patch:
                current_patch = new_patch
                await self.message_tft_servers()
            await sleep(random.uniform(700,900))

    async def message_tft_servers(self):
        patch_data = await get_recent_tft_data()
        approved_guilds = self.guild_db.get_approved_guilds()
        for guild in self.guilds:
            if guild.id in approved_guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        try:
                            await channel.send(f'Found new tft patch!')
                            await self.send_tft_data(patch_data,channel)
                        except discord.Forbidden:
                            print(f"Missing permissions in {guild.name}")
                        except discord.HTTPException as e:
                            print(f"Failed to send message in {guild.name}: {e}")
                        break 

    async def check_tft_link(self, message):
        split_msg = message[5:].split('.')
        if len(split_msg) < 2 or len(split_msg) > 3:
            return ''
        if len(split_msg) == 2:
            tft_link = f"https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-{split_msg[0]}-{split_msg[1]}-notes/"
            if TFT_PATCH_NOTES_REGEX.match(tft_link):
                return tft_link
        else:
            tft_link = f"https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-{split_msg[0]}-{split_msg[1]}-notes-{split_msg[2]}/"
            if TFT_PATCH_YEAR_NOTES_REGEX.match(tft_link):
                return tft_link
        return ''

if __name__ == '__main__':
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        intents.voice_states = True
        client = TFTBotClient(intents=intents)
        load_dotenv()
        tkn = os.getenv('DISCORDBOTTOKEN')
        client.run(token=tkn)
