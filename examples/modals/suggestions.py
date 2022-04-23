import re
import asyncio
import discord
from discord.ext import commands

from discord import ComponentInteraction, Modal, TextInput, Button, ButtonStyle


class ModalSuggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def send_suggestmsg(self, ctx):
        embed = discord.Embed(title='Suggestions', description='Click the button below to add a new suggestion',
                              color=discord.Color.orange())
        embed.add_field(
            name='Note:',
            value='If you want to include images you must do this via. an file-hoster like '
                  '[tixte](https://tixte.com/?ref=mccoder-py-needs.to-sleep.xyz) or [imgur](https://imgur.com/).'
        )
        embed.set_footer(
            text='**⚠The image link must be a direct(direct link to the file) link '
                 '(These usually do not form an embed in Discord and look like normal uploaded files)⚠.**'
        )
        await ctx.send(embed=embed, components=[[
            Button(label='New Suggestion',
                   custom_id='suggestion:new',
                   style=ButtonStyle.blurple,
                   emoji='💡')
        ]])
        discord.PartialMessage(channel=ctx.channel, id=ctx.nesssage.reference.message_id)

    @commands.Cog.on_click(r'^suggestion:new$')
    async def new_suggestion(self, interaction: ComponentInteraction, button):
        suggest_modal = Modal(custom_id=f'suggestion:new:{interaction.id}:{interaction.author.id}',
                              title='Create a new Suggestion.',
                              components=[TextInput(custom_id='short_description',
                                                    label='Short description of your suggestion',
                                                    style=1,
                                                    min_length=10,
                                                    max_length=256,
                                                    placeholder='Implement new Modals'),
                                          TextInput(custom_id='description',
                                                    label='Description',
                                                    style=2,
                                                    min_length=20,
                                                    placeholder='Discord released ... that should be implemented here.'),
                                          TextInput(custom_id='wy',
                                                    label='Wy this feature should be changed/implemented',
                                                    style=2,
                                                    min_length=20,
                                                    max_length=1000,
                                                    required=False,
                                                    placeholder='Because with this new feature you can make some stuff like this.')
                                          ])
        await interaction.respond_with_modal(modal=suggest_modal)
        try:
            inter: discord.ModalSubmitInteraction = await self.bot.wait_for(
                'modal_submit',
                check=lambda ms: ms.custom_id == f'suggestion:new:{interaction.id}:{interaction.author.id}',
                timeout=5000
            )
        except asyncio.TimeoutError:
            pass
        else:
            description: str = inter.get_field('description').value
            image_urls = re.findall(r"(?P<url>https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4))",
                                    description)  # i know this is actually not the best RegEx
            for index, url in enumerate(image_urls):
                if index == 0:
                    description = description.replace(url[0],
                                                      f'[see {"video" if url[0].endswith(".mp4") else "image"} below]')
                else:
                    description = description.replace(url[0], f'[attachment-{index}]')

            embed = discord.Embed(
                title=inter.get_field('short_description').value,
                description=f"```\n{description}\n```"
            )
            if wy := inter.get_field('wy').value:
                embed.add_field(name='Wy should this be added/updated?',
                                value=f'```\n{wy}\n```',
                                inline=False
                                )
            embed.set_author(icon_url=inter.author.avatar_url,
                             name=str(inter.author),
                             url=f'https://discord.com/users/{inter.author.id}'
                             )
            embed.set_footer(text='See the attachments in the tread below')
            content = None
            if image_urls:
                url = image_urls.pop(0)[0]
                if url.endswith('.mp4'):
                    content = url
                else:
                    embed.set_image(url=url)
            mes = await inter.respond(embed=embed,
                                      components=[[Button(label='delete suggestion',
                                                          custom_id='suggestion:delete',
                                                          style=ButtonStyle.red,
                                                          emoji='🗑️')
                                                   ]]
                                      )
            url_msg = None
            if content:
                url_msg = await inter.channel.send(content)
            if url_msg:
                await mes.edit(embed=embed,
                               components=[[Button(label='delete suggestion',
                                                   custom_id=f'suggestion:delete:{url_msg.id}',
                                                   style=ButtonStyle.red,
                                                   emoji='🗑️')
                                            ]]
                               )
            thread = await mes.create_thread(
                name=inter.get_field('short_description').value,
                reason='Thread was created automatically as a result of creating a suggestion'
            )
            if image_urls:
                await thread.send(
                    embed=discord.Embed(
                        title='Here are the other images provided in the suggestion',
                        color=discord.Color.green()
                    ))
                await thread.send(
                    '\n'.join([f'**`attachment-{index + 1}:`** {url[0]}' for index, url in enumerate(image_urls)]))

    @commands.Cog.on_click(r'^suggestion:delete(:\d*)?$')
    async def delete_suggestion(self, interaction: ComponentInteraction, button):
        if interaction.author.id == int(
                interaction.message.embeds[0].author.url.split('/')[-1]) or interaction.author.permissions_in(
                interaction.channel).manage_messages:
            before_embeds = interaction.message.embeds
            before_components = interaction.message.components
            if match := re.search(r'(?P<url_msg_id>[\d]+)', [c for c in interaction.message.all_buttons][0].custom_id):
                url_msg = discord.PartialMessage(channel=interaction.channel, id=int(match.group('url_msg_id')))
            else:
                url_msg = None
            msg = await interaction.edit(embed=discord.Embed(
                title='⚠Warning: ❗This action is not reversible❗⚠',
                description='Are you sure you want to delete this suggestion and the thread associated with it?'
            ),
                components=[
                    [
                        Button(label='Yes', custom_id='suggestion:delete-yes', style=ButtonStyle.red),
                        Button(label='No', custom_id='suggestion:delete-cancel', style=ButtonStyle.red)
                    ]]
            )
            try:
                inter, but = await self.bot.wait_for(
                    'raw_button_click',
                    check=lambda i, b: i.author == interaction.author and i.message.id == msg.id,
                    timeout=10
                )
            except asyncio.TimeoutError:
                await msg.edit(embeds=before_embeds, components=before_components)
            else:
                if but.custom_id == 'suggestion:delete-yes':
                    if interaction.message.thread:
                        await interaction.message.thread.delete(
                            reason=f'The associated suggestion for this thread was deleted by {interaction.author}.')
                    await inter.edit(embed=discord.Embed(title='This message will be deleted in 3 Seconds.',
                                                         color=discord.Color.green()), delete_after=4)
                    if url_msg:
                        await url_msg.delete(delay=4)
                else:
                    await inter.edit(embeds=before_embeds, components=before_components)


def setup(bot):
    bot.add_cog(ModalSuggestions(bot))
