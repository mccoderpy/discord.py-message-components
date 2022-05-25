import re
import logging
import asyncio
from typing import Union, Optional, List

import aiohttp
import discord
from discord.ext import commands
from logging.handlers import HTTPHandler
from discord import SlashCommandOption as SlashOption, SlashCommandOptionChoice as Choice, ComponentInteraction, Modal, TextInput, Button, ButtonStyle, ModalSubmitInteraction, Localizations
from .localized_strings import DATA

# log = logging.getLogger(__name__)
# log.addHandler(WebHookLogger('discord.com:443', 'https://canary.discord.com/api/webhooks/968875098192904263/E2-5aHFLjXayJ3QuXVaqxsYc5CCF2LxighcKExZxMiLrsYJpOY8Fs1kgrtiUx7mnRHl_'))


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
            inter: discord.ModalSubmitInteraction = await self.bot.wait_for(
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

    # @commands.Cog.on_submit(r'^suggestion:new:\d+:\d+$')
    async def suggestions_modal_submit_callback(self, interaction: ModalSubmitInteraction):
        print(interaction.data.components)

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

    @commands.Cog.slash_command(
        base_name='poll',
        base_desc='📋 | Manages polls on this server',
        name='create',
        description='🆕 | Create a new poll',
        base_name_localizations=Localizations(german='umfrage'),
        base_desc_localizations=Localizations(german='📋 | Verwalte Umfragen auf diesem Server'),
        name_localizations=Localizations(german='erstellen'),
        description_localizations=Localizations(german='🆕 | Erstelle eine neue Umfrage'),
        default_required_permissions=discord.Permissions(manage_messages=True, manage_events=True),
        options=[
            SlashOption(
                str,
                'title',
                'The title of the poll',
                description_localizations=Localizations(german='Der Titel der Umfrage')
            ),
            SlashOption(
                str,
                'description',
                'The description of the poll',
                name_localizations=Localizations(german='beschreibung'),
                description_localizations=Localizations(german='Die Beschreibung der Umfrage'),
                required=False
            ),
            SlashOption(
                str,
                'voting-type',
                'How the choices are listed and selectable | Default: Button',
                name_localizations=Localizations(german='art-der-stimmabgabe'),
                description_localizations=Localizations(
                    german='Wie die Möglichkeiten aufgelistet und wählbar sind | Standard: Button'
                ),
                choices=[
                    Choice('Button', 'button'),
                    Choice('Select Menu', 'select menu'),
                    Choice('Emoji Reaction', 'reaction')
                ],
                required=False
            ),
            SlashOption(
                int,
                'possible-votes',
                'How many votes can be cast',
                name_localizations=Localizations(german='abgebbare-stimmen'),
                description_localizations=Localizations(german='Wie viele Stimmen abgegeben werden können'),
                min_value=1,
                max_value=25,
                required=False
            ),
            SlashOption(
                int,
                'minimum-votes',
                'How many votes must be cast',
                name_localizations=Localizations(german='mindestens-abzugebende-stimmen'),
                description_localizations=Localizations(german='Wie viele Stimmen abgegeben werden müssen'),
                min_value=1,
                max_value=25,
                required=False
            ),
            SlashOption(
                str,
                'roles',
                'Limits the poll to the specified roles',
                name_localizations=Localizations(german='rollen'),
                description_localizations=Localizations(german='Beschränkt die Stimmabgabe auf die angegebenen Rollen'),
                required=False,
                converter=commands.Greedy[discord.Role]
            ),
            SlashOption(
                discord.abc.GuildChannel,
                'channel',
                'The channel to create the poll in. Default to the current channel',
                name_localizations=Localizations(german='kanal'),
                description_localizations=Localizations(
                    german='Der channel in dem die Umfrage stattfinden soll'
                ),
                required=False,
                channel_types=[discord.TextChannel, discord.ThreadChannel]
            ),
            SlashOption(
                bool,
                'reason-needed',
                'Whether the user has to give a reason for his choice. The questions for this can be defined',
                name_localizations=Localizations(german='auswahl-begründen'),
                description_localizations=Localizations(
                    german='Ob der Nutzer eine Begründung für seine Wahl abgeben muss. Die Fragen dazu können festgelegt werden'
                ),
                required=False
            ),
            SlashOption(
                bool,
                'anonymous-poll',
                'In an anonymous survey, the name of the creator will not be displayed.',
                name_localizations=Localizations(german='anonyme-umfrage'),
                description_localizations=Localizations(
                    german='Bei einer anonymen Umfrage wird der Name des Erstellers nicht angezeigt'
                ),
                required=False
            ),
            SlashOption(
                bool,
                'users-can-add-options',
                'Whether users can add options to the poll',
                name_localizations=Localizations(german='user-können-optionen-hinzufügen'),
                description_localizations=Localizations(
                    german='Ob die Benutzer Optionen zur Umfrage hinzufügen können'
                ),
                required=False
            ),
            SlashOption(
                bool,
                'create-discussion-thread',
                'Whether a thread for discussions should be created for this poll',
                name_localizations=Localizations(german='discussions-thread-erstellen'),
                description_localizations=Localizations(
                    german='Ob ein Thread für Diskussionen für diese Umfrage erstellt werden soll'
                ),
                required=False
            ),
            SlashOption(
                str,
                'embed-color',
                'The color the embed of the poll should have',
                name_localizations=Localizations(german='embed-farbe'),
                description_localizations=Localizations(
                    german='Die Farbe, die das Embed der Umfrage haben soll'
                ),
                required=False,
                converter=commands.ColorConverter
            )
        ],
        connector={
            'voting-type': 'voting_type',
            'possible-votes': 'max_choices',
            'minimum-votes': 'min_choices',
            'reason-needed': 'reason_needed',
            'anonymous-poll': 'anonymous',
            'users-can-add-options': 'users_can_add_options',
            'create-discussion-thread': 'create_discussion_thread',
            'embed-color': 'color'
        },
        guild_ids=[852871920411475968])
    async def create_poll(
            self,
            ctx: discord.ApplicationCommandInteraction,
            title: str,
            description: Optional[str] = None,
            voting_type: Optional[str] = 'button',
            max_choices: Optional[int] = 1,
            min_choices: Optional[int] = 1,
            roles: Optional[List[discord.Role]] = [],
            channel: Optional[Union[discord.TextChannel, discord.ThreadChannel]] = None,
            reason_needed: Optional[bool] = False,
            anonymous: Optional[bool] = False,
            users_can_add_options: Optional[bool] = False,
            create_discussion_thread: Optional[bool] = False,
            color: Optional[discord.Color] = discord.Color.default()
    ):
        data = {}
        __located_resp = DATA['slash_command_responses']['poll_create']
        poll_id = str(ctx.id)
        poll_embed = discord.Embed(
            title=title,
            color=color
        )
        if description:
            poll_embed.description = description
        components = [
            [
                Button(
                    label='Add option',
                    custom_id=f'poll:{poll_id}:add-option',
                    style=ButtonStyle.blurple,
                    emoji='<:listplus:977234311130517564>'
                ),
                Button(
                    label='Start poll',
                    custom_id=f'poll:create:{poll_id}:start',
                    style=ButtonStyle.blurple,
                    emoji='✅'
                ),

            ]
        ]
        if reason_needed:
            located_resp_rm = __located_resp['setups']['reason_modal']
            modal = Modal(
                custom_id=f'poll:create:{poll_id}:reason_modal:setup',
                title=located_resp_rm['title'].from_target(ctx),
                components=[
                    TextInput(
                        label=located_resp_rm['fields']['label']['label'].from_target(ctx),
                        custom_id='label',
                        style=2,
                        max_length=45,
                        value=located_resp_rm['fields']['label']['value'].from_target(ctx),
                        placeholder=located_resp_rm['fields']['label']['placeholder'].from_target(ctx)
                    ),
                    TextInput(
                        label=located_resp_rm['fields']['value']['label'].from_target(ctx),
                        custom_id='value',
                        style=2,
                        max_length=4000,
                        required=False,
                        value=located_resp_rm['fields']['value']['value'].from_target(ctx),
                        placeholder=located_resp_rm['fields']['value']['placeholder'].from_target(ctx)
                    ),
                    TextInput(
                        label=located_resp_rm['fields']['placeholder']['label'].from_target(ctx),
                        custom_id='placeholder',
                        style=2,
                        max_length=100,
                        required=False,
                        value=located_resp_rm['fields']['placeholder']['value'].from_target(ctx),
                        placeholder=located_resp_rm['fields']['placeholder']['placeholder'].from_target(ctx)
                    )

                ]
            )
            await ctx.respond_with_modal(modal)
            try:
                reason_modal_inter: discord.ModalSubmitInteraction = await self.bot.wait_for(
                    'modal_submit',
                    check=lambda m: m.custom_id == f'poll:create:{poll_id}:reason_modal:setup',
                    timeout=600
                )
            except asyncio.TimeoutError:
                return await ctx.respond(
                    embed=discord.Embed(
                        title='Your answer took to long. This poll setup is cancelled.',
                        color=discord.Color.red()
                    )
                )
            else:
                await reason_modal_inter.respond('Successfully set up reason modal.', hidden=True)
                data['reason_modal'] = reason_modal_inter.fields
        if roles:
            await ctx.respond('\n'.join([r.mention for r in roles]), hidden=True)


def setup(bot):
    bot.add_cog(ModalSuggestions(bot))
