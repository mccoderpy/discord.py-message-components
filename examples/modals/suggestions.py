import re
import asyncio
import discord
from discord.ext import commands

from discord import ComponentInteraction, ModalSubmitInteraction, Modal, TextInput, Button, ButtonStyle


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
            value='If you want to include images/video you must do this via. a file hoster like '
                  '[tixte](https://tixte.com/?ref=mccoder-py-needs.to-sleep.xyz) or [imgur](https://imgur.com/).'
        )
        embed.set_footer(
            text='⚠The image link must be a direct(direct link to the file) link '
                 '(These usually do not form an embed in Discord and look like normal uploaded files)⚠.'
        )
        await ctx.send(embed=embed, components=[[
            Button(label='New Suggestion',
                   custom_id='suggestion:new',
                   style=ButtonStyle.blurple,
                   emoji='💡')
        ]])

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
                                                    placeholder='Discord released -x- that should be implemented here.'),
                                          TextInput(custom_id='wy',
                                                    label='Wy this feature should be changed/implemented',
                                                    style=2,
                                                    min_length=20,
                                                    max_length=1000,
                                                    required=False,
                                                    placeholder='With this new feature you can make -x-.')
                                          ])
        await interaction.respond_with_modal(modal=suggest_modal)
        try:
            inter: ModalSubmitInteraction = await self.bot.wait_for(
                'modal_submit',
                check=lambda ms: ms.custom_id == f'suggestion:new:{interaction.id}:{interaction.author.id}',
                timeout=5000
            )
        except asyncio.TimeoutError:
            pass
        else:
            description: str = inter.get_field('description').value
            image_urls = re.findall(
                r"(?P<url>https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4))",
                description
            )  # I know this is actually not the best RegEx
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
            mes = await inter.respond(
                embed=embed,
                components=[
                    [
                        Button(
                            label='delete suggestion',
                            custom_id=f'suggestion:delete',
                            style=ButtonStyle.red,
                            emoji='🗑️'
                        ),
                        Button(
                            label='edit suggestion',
                            custom_id=f'suggestion:edit:{inter.author.id}',
                            style=ButtonStyle.grey,
                            emoji='↩'
                        )
                    ]
                ]
            )
            url_msg = None
            if content:
                url_msg = await inter.channel.send(content)
            if url_msg:
                await mes.edit(
                    components=[
                        [
                            Button(
                                label='delete suggestion',
                                custom_id=f'suggestion:delete:{url_msg.id}',
                                style=ButtonStyle.red,
                                emoji='🗑️'
                            ),
                            Button(
                                label='edit suggestion',
                                custom_id=f'suggestion:edit:{inter.author.id}',
                                style=ButtonStyle.grey,
                                emoji='↩'
                            )
                        ]
                    ]
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
                    await inter.edit(
                        embed=discord.Embed(
                            title='This message will be deleted in 3 Seconds.',
                            color=discord.Color.green()),
                        components=[],
                        delete_after=4
                    )
                    if url_msg:
                        await url_msg.delete(delay=4)
                else:
                    await inter.edit(embeds=before_embeds, components=before_components)

    @commands.Cog.on_click(r'^suggestion:edit(:\d*)?$')
    async def edit_suggestion(self, interaction: ComponentInteraction, button):
        if interaction.author.id == int(
                interaction.message.embeds[0].author.url.split('/')[-1]) or interaction.author.permissions_in(
            interaction.channel).manage_messages:
            embed = interaction.message.embeds[0]
            old_short_description = embed.title
            old_description = embed.description
            url_msg = None
            image_messages =  []
            if re.search(r'(\[see video below])', old_description):
                if match := re.search(r'(?P<url_msg_id>[\d]+)', [c for c in interaction.message.all_buttons][0].custom_id):
                    url_msg = await discord.PartialMessage(channel=interaction.channel, id=int(match.group('url_msg_id'))).fetch()
                    old_description = old_description.replace('[see video below]', url_msg.content)
            if re.search(r'(\[see image below])', old_description):
                old_description = old_description.replace('[see image below]', embed.image.url)
            if attachments:= re.findall(r'\[attachment-\d{1,2}]', old_description):
                thread = interaction.message.thread
                image_messages = await thread.history(after=thread.starter_message, limit=3).flatten()
                urls =  re.findall(r"(https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4|mov))", image_messages[-1].content)
                for attachment, url in zip(attachments, urls):
                    old_description = old_description.replace(attachment, url[0])
            old_wy = embed.fields[-1] or discord.embeds.EmbedProxy({'value': ''})
            suggest_modal = Modal(custom_id=f'suggestion:edit:{interaction.id}:{interaction.author.id}',
                                  title='Update Suggestion.',
                                  components=[TextInput(
                                      custom_id='short_description',
                                      label='Short description of your suggestion',
                                      style=1,
                                      min_length=10,
                                      max_length=256,
                                      placeholder='Implement new Modals',
                                      value=old_short_description
                                  ),
                                      TextInput(
                                          custom_id='description',
                                          label='Description',
                                          style=2,
                                          min_length=20,
                                          placeholder='Discord released -x- that should be implemented here.',
                                          value=old_description.replace('```\n', '').replace('\n```', '')
                                      ),
                                      TextInput(
                                          custom_id='wy',
                                          label='Wy this feature should be changed/implemented',
                                          style=2,
                                          min_length=20,
                                          max_length=1000,
                                          required=False,
                                          placeholder='With this new feature you can make -x-.',
                                          value=old_wy.value.replace('```\n', '').replace('\n```', '')
                                      )
                                  ])
            await interaction.respond_with_modal(modal=suggest_modal)
            try:
                inter: discord.ModalSubmitInteraction = await self.bot.wait_for(
                    'modal_submit',
                    check=lambda ms: ms.custom_id == f'suggestion:edit:{interaction.id}:{interaction.author.id}',
                    timeout=5000
                )
            except asyncio.TimeoutError:
                pass
            else:
                short_description, description, wy = list(map(lambda f: f.value, inter.fields))
                if short_description == old_short_description and description == old_description and wy == old_wy.value:
                    return await inter.respond('Nothing changed', hidden=True)

                await inter.defer(hidden=True)
                image_urls = re.findall(r"(https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4))", description)
                attachments_changed = image_urls != re.findall(r"(https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4|mov))", old_description)
                for index, url in enumerate(image_urls):
                    if index == 0:
                        description = description.replace(url[0],
                                                          f'[see {"video" if url[0].endswith((".mp4", ".mov")) else "image"} below]')
                    else:
                        description = description.replace(url[0], f'[attachment-{index}]')

                embed = discord.Embed(
                    title=short_description,
                    description=f"```\n{description}\n```"
                )
                if wy:
                    embed.add_field(
                        name='Wy should this be added/updated?',
                        value=f'```\n{wy}\n```',
                        inline=False
                    )
                embed.set_author(
                    icon_url=inter.author.avatar_url,
                    name=str(inter.author),
                    url=f'https://discord.com/users/{inter.author.id}'
                )
                embed.set_footer(text='See the attachments in the tread below')
                content = None
                if image_urls:
                    url = image_urls.pop(0)[0]
                    if url.endswith(('.mp4', '.mov')):
                        content = url
                    else:
                        embed.set_image(url=url)
                await interaction.message.edit(embed=embed)
                if attachments_changed:
                    if content:
                        method = url_msg.edit if url_msg else (inter.channel.send if (interaction.message.id == interaction.channel.last_message_id) else image_urls.insert(0, content))
                        if method:
                            new_url_msg = await method(content=content)
                            if not url_msg:
                                await interaction.message.edit(
                                    components=[
                                        [
                                            Button(
                                                label='delete suggestion',
                                                custom_id=f'suggestion:delete:{new_url_msg.id}',
                                                style=ButtonStyle.red,
                                                emoji='🗑️'
                                            ),
                                            Button(
                                                label='edit suggestion',
                                                custom_id=f'suggestion:edit:{inter.author.id}',
                                                style=ButtonStyle.grey,
                                                emoji='↩'
                                            )
                                        ]
                                    ]
                                )
                    else:
                        if url_msg:
                            await url_msg.delete()
                            await interaction.message.edit(
                                components=[
                                    [
                                        Button(
                                            label='delete suggestion',
                                            custom_id=f'suggestion:delete',
                                            style=ButtonStyle.red,
                                            emoji='🗑️'
                                        ),
                                        Button(
                                            label='edit suggestion',
                                            custom_id=f'suggestion:edit:{inter.author.id}',
                                            style=ButtonStyle.grey,
                                            emoji='↩'
                                        )
                                    ]
                                ]
                            )
                    thread = inter.message.thread
                    if not len(image_messages) <= 4 or not re.match(
                        r"(\*\*`attachment-\d{1,2}:`\*\* https://[^\s]+\.(jpeg|jpg|webp|png|gif|mp4|mov)\n?)+",
                        image_messages[-1].content
                    ) or not image_messages[-1].author.id == inter.bot.user.id:
                        image_messages = None
                    if image_urls:
                        method = image_messages[-1].edit if image_messages else (thread.send if thread.message_count <= 3 else None)
                        if method is None:
                            await thread.send(f"**These attachments have been added**\n" + '\n'.join([f'**`attachment-{index + 1}:`** {url[0]}' for index, url in enumerate(image_urls)]))
                        else:
                            if thread.message_count < 2:
                                await thread.send(
                                    embed=discord.Embed(
                                        title='Here are the other images provided in the suggestion',
                                        color=discord.Color.green()
                                    ))
                            await method(content='\n'.join([f'**`attachment-{index + 1}:`** {url[0]}' for index, url in enumerate(image_urls)]))
                    else:
                        if image_messages:
                            for m in image_messages[1:]:
                                await m.delete()
                await inter.respond('Successful updated the suggestion', hidden=True)

def setup(bot):
    bot.add_cog(ModalSuggestions(bot))
