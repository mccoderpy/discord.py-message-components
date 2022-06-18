import itertools
import re
import logging
import asyncio
from collections import namedtuple
from typing import Union, Optional, List, Tuple, Dict, TYPE_CHECKING, Any

import aiohttp
import content as content

import discord
from discord.ext import commands
from logging.handlers import HTTPHandler
from discord import SlashCommandOption as SlashOption, SlashCommandOptionChoice as Choice, ComponentInteraction, Modal, \
    TextInput, Button, ButtonStyle, ModalSubmitInteraction, Localizations, Role, TextChannel, ThreadChannel, Color, \
    SelectMenu, SelectOption
from .localized_strings import DATA

# log = logging.getLogger(__name__)
# log.addHandler(WebHookLogger('discord.com:443', 'https://canary.discord.com/api/webhooks/968875098192904263/E2-5aHFLjXayJ3QuXVaqxsYc5CCF2LxighcKExZxMiLrsYJpOY8Fs1kgrtiUx7mnRHl_'))


class NamedDict:
    __slots__ = {'__name__', '__dict__'}

    def __init__(self, name: str = 'NamedDict', layer: dict = {}):
        self.__name__ = name
        self.__dict__.update(layer)
        self.__dict__['__shape_set__'] = 'shape' in layer
        self.__slots__.update([k for k in layer.keys()])

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return f'{self.__name__}(%s)' % ', '.join(('%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')))

    def __getattr__(self, attr):
        if attr == 'shape':
            if not self.__dict__['__shape_set__']:
                return None
        try:
            return self.__dict__[attr]
        except KeyError:
            setattr(self, attr, NamedDict())
            return self.__dict__[attr]

    def __setattr__(self, key, value):
        self.__slots__.add(key)
        self.__dict__[key] = value


    def __delattr__(self, item):
        self.__slots__.remove(item)
        self.__dict__.pop(item)

    """def __class_getitem__(cls, item: Union[List[Union[str, Tuple[str, type]]], Dict[str, type]]):
        obj = namedtuple('NamedDict', [i for i in item])
        __annotations__ = obj.__slots__.__dict__
        if isinstance(item, list):
            for o in item:
                if isinstance(o, str):
                    __annotations__[o] = Any
                elif isinstance(o, tuple):
                    __annotations__[o[0]] = o[1]
        elif isinstance(item, dict):
            for k, v in item.items():
                __annotations__[k] = v
        return obj
    """

    def __class_getitem__(cls, item: List[Tuple[str, Any]]):
        if TYPE_CHECKING:
            return namedtuple(cls.__class__.__name__, ' '.join([i[0] for i in item]))
        return item

    def _to_dict(self, include_names: bool = False):
        data = {}
        for k, v in self.__dict__.items():
            if isinstance(v, NamedDict):
                data[k] = v._to_dict(include_names=include_names)
            else:
                if k != '__shape_set__':
                    if k == '__name__' and not include_names:
                        continue
                    data[k] = v
        return data

    @classmethod
    def _from_dict(cls, data: dict):
        named = cls(name=data.pop('__name__', 'NamedDict'))
        _dict = named.__dict__
        for k, v in data.items():
            named.__slots__.add(k)
            if isinstance(v, dict):
                _dict[k] = cls._from_dict(v)
            else:
                _dict[k] = v
        return named


class ModalSuggestions(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.poll_setups: Dict[str, NamedDict] = {}
        self.active_polls: Dict[str, NamedDict] = {}
        from .localized_strings import DATA

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
                                          TextInput(custom_id='why',
                                                    label='Reason for this suggestion',
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
            if description.startswith('```'):
                if description.endswith('```'):
                    pass
                else:
                    description += '\n```'
            else:
                if description.endswith('```'):
                    description = '```\n' + description
                else:
                    description = f'```\n{description}\n```'
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
                description=description
            )
            if why := inter.get_field('why').value:
                embed.add_field(name='Why should this be added/updated?',
                                value=f'```\n{why}\n```',
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
            old_why = embed.fields[-1] or discord.embeds.EmbedProxy({'value': ''})
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
                                          custom_id='why',
                                          label='Reason for this suggestion',
                                          style=2,
                                          min_length=20,
                                          max_length=1000,
                                          required=False,
                                          placeholder='With this new feature you can make -x-.',
                                          value=old_why.value.replace('```\n', '').replace('\n```', '')
                                      )
                                  ])
            await interaction.respond_with_modal(modal=suggest_modal)
            try:
                inter: ModalSubmitInteraction = await self.bot.wait_for(
                    'modal_submit',
                    check=lambda ms: ms.custom_id == f'suggestion:edit:{interaction.id}:{interaction.author.id}',
                    timeout=5000
                )
            except asyncio.TimeoutError:
                pass
            else:
                short_description, description, why = list(map(lambda f: f.value, inter.fields))
                if short_description == old_short_description and description == old_description and why == old_why.value:
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
                if description.startswith('```'):
                    if description.endswith('```'):
                        pass
                    else:
                        description += '\n```'
                else:
                    if description.endswith('```'):
                        description = '```\n' + description
                    else:
                        description = f'```\n{description}\n```'
                embed = discord.Embed(
                    title=short_description,
                    description=description
                )
                if why:
                    embed.add_field(
                        name='Why should this be added/updated?',
                        value=f'```\n{why}\n```',
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
    poll_data_attributes = [
        ('voting_type', str),
        ('roles', Optional[List[Role]]),
        ('channel', Union[TextChannel, ThreadChannel]),
        ('max_choices', int),
        ('min_choices', int),
        ('reason_needed', int),
        ('anonymous', bool),
        ('users_can_add_options', bool),
        ('create_discussion_thread', bool),
        ('color', discord.Color),
        ('reason_modal', NamedDict('ReasonModal')),
        ('options', List[NamedDict])
    ]

    def get_poll(self, custom_id: str, from_setup: bool = False) -> NamedDict[poll_data_attributes]:
        id_found = re.search(r':(?P<id>\d+).*', custom_id)
        if not id_found:
            raise ValueError(f'{custom_id} contains no valid ID.')
        if from_setup:
            return self.poll_setups[str(id_found.group('id'))]
        return self.active_polls[str(id_found.group('id'))]

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
                int,
                'reason-needed',
                'Whether the user has to give a reason for his choice. The questions for this can be defined',
                name_localizations=Localizations(
                    german='auswahl-begründen'
                ),
                description_localizations=Localizations(
                    german='Ob der Nutzer eine Begründung für seine Wahl abgeben muss. Die Fragen dazu können festgelegt werden'
                ),
                choices=[
                    Choice(name='No', value=0, name_localizations=Localizations(german='Nein')),
                    Choice(name='Yes', value=1, name_localizations=Localizations(german='Ja')),
                    Choice(name='Yes (Optional)', value=2, name_localizations=Localizations(german='Ja (Optional)'))
                ],
                required=False
            ),
            SlashOption(
                discord.OptionType.channel,
                'send-reasons-in',
                'Where the reasons provided by the users should send to(only if reason-needed is not No)',
                name_localizations=Localizations(german='sende-begründungen-in'),
                description_localizations=Localizations(
                    german='Der Kanal wo die Begründungen hingeschickt werden sollen(wenn auswahl-begründen nicht Nein ist)'
                ),
                required=False,
                channel_types=[discord.TextChannel, discord.ThreadChannel]
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
                'ping',
                'If any, and when what targets should be pinged; default: Nobody',
                name_localizations=Localizations(german='erwähne'),
                description_localizations=Localizations(
                    german='Ob und wenn ja, wer erwähnt werden soll; Standard: Niemanden'
                ),
                choices=[
                    Choice(
                        name='@everyone role',
                        value='@everyone',
                        name_localizations=Localizations(
                            german='@everyone Rolle (Jeder)'
                        )
                    ),
                    Choice(
                        name='@here role (any currently online member)',
                        value='@here',
                        name_localizations=Localizations(
                            german='@here Rolle (Jeder Member der gerade online ist)'
                        )
                    ),
                    Choice(
                        name='All roles provided via. role option',
                        value='roles',
                        name_localizations=Localizations(
                            german='Alle via. rollen angegebene Rollen'
                        )
                    ),
                    Choice(
                        name='Nobody (default)',
                        value='none',
                        name_localizations=Localizations(
                            german='Niemanden'
                        )
                    )
                ],
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
            'send-reasons-in': 'send_reasons_in',
            'anonymous-poll': 'anonymous',
            'users-can-add-options': 'users_can_add_options',
            'create-discussion-thread': 'create_discussion_thread',
            'embed-color': 'color'
        },
        guild_ids=[852871920411475968],

    )
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
            reason_needed: Optional[int] = 0,
            send_reasons_in: Optional[Union[discord.TextChannel, discord.ThreadChannel]] = None,
            anonymous: Optional[bool] = False,
            users_can_add_options: Optional[bool] = False,
            create_discussion_thread: Optional[bool] = False,
            ping: str = 'none',
            color: Optional[discord.Color] = discord.Color.default()
    ):
        __located_resp = DATA['slash_command_responses']['poll_create']
        poll_id = str(ctx.id)
        channel = channel or ctx.channel
        self.poll_setups[poll_id] = data = NamedDict('PollSetupData')
        data.id = str(ctx.id)
        data.author = ctx.author
        data.author_id = ctx.author.id
        data.title = title
        data.description = description
        data.voting_type = voting_type
        data.roles = roles
        data.channel = channel
        data.max_choices = max_choices
        data.min_choices = min_choices
        data.reason_needed = reason_needed
        data.reasons_channel = send_reasons_in
        data.anonymous = anonymous
        data.users_can_add_options = users_can_add_options
        data.create_discussion_thread = create_discussion_thread
        data.color = color
        data.options = []
        data.option_names = []

        data.embed = poll_embed = discord.Embed(
            title=title,
            color=color
        )
        if description:
            poll_embed.description = description
        components = [
            [
                Button(
                    label='Add option',
                    custom_id=f'poll:create:{poll_id}:add-option',
                    style=ButtonStyle.blurple,
                    emoji='<:listplus:977234311130517564>'
                ),
                Button(
                    label='Start poll',
                    custom_id=f'poll:create:{poll_id}:start',
                    style=ButtonStyle.green,
                    emoji='✅'
                ),

            ]
        ]
        if reason_needed:
            components[0].insert(1, Button(
                label='Edit reason modal',
                custom_id=f'poll:create:{poll_id}:edit-reason-modal',
                style=ButtonStyle.blurple
            ))
        if ping != 'none':
            if ping == 'roles':
                ping = ', '.join([role.mention for role in roles])
            data.ping = ping
            poll_embed.add_field(
                name='Roles that will be pinged',
                value=ping
            )
        poll_embed.add_field(
            name='Poll will send to',
            value=channel.mention
        )
        if reason_needed != 0:
            if send_reasons_in:
                poll_embed.add_field(
                    name='Reasons will send to',
                    value=send_reasons_in.mention
                )
            else:
                poll_embed.add_field(
                    name='Reasons will send to',
                    value=f'This channel, consider providing a other channel using the `send-reasons-to` option.'
                )
                data.reasons_channel = channel


        interaction = ctx
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
            await interaction.respond_with_modal(modal)
            try:
                interaction: ModalSubmitInteraction = await self.bot.wait_for(
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
                data.reason_modal.label = interaction.get_field('label')
                data.reason_modal.value = interaction.get_field('value')
                data.reason_modal.placeholder = interaction.get_field('placeholder')
        await interaction.respond(embed=poll_embed, components=components, hidden=True)

    @commands.Cog.on_click(r'^poll:create:\d+:add-option$')
    async def poll_create_add_option(self, ctx: ComponentInteraction, button):
        __located_resp = DATA['button_responses']['poll_create']['add_option']
        data: NamedDict[ModalSuggestions.poll_data_attributes] = self.get_poll(button.custom_id, from_setup=True)
        if data.voting_type == 'select menu':
            await ctx.respond_with_modal(
                Modal(
                    title=__located_resp['select menu']['title'].from_target(ctx),
                    custom_id=f'poll:add-option:{ctx.id}',
                    components=[
                        TextInput(
                            label=__located_resp['select menu']['fields']['name']['label'].from_target(ctx),
                            custom_id='option-name',
                            placeholder=__located_resp['select menu']['fields']['name']['placeholder'].from_target(ctx),
                            max_length=50,
                            min_length=1,
                        ),
                        TextInput(
                            label=__located_resp['select menu']['fields']['description']['label'].from_target(ctx),
                            custom_id='option-description',
                            placeholder=__located_resp['select menu']['fields']['description']['placeholder'].from_target(ctx),
                            max_length=(100 - (len(f' [Poll author]' + (f'({ctx.author})' if not data.anonymous else "")) if ctx.author == data.author else len(f' [{ctx.author}]'))),
                            min_length=10,
                            required=False
                        )
                    ]
                )
            )
            try:
                inter: ModalSubmitInteraction = await self.bot.wait_for('modal_submit', check=lambda i: i.custom_id == f'poll:add-option:{ctx.id}', timeout=600)
            except asyncio.TimeoutError:
                return await ctx.channel.send(f'{ctx.author.mention}: Adding of option cancelled because of taking to long.')
            else:
                name = inter.get_field('option-name').value
                description = inter.get_field('option-description').value
                if name in data.option_names:
                    return await inter.respond(
                        embed=discord.Embed(
                            title=__located_resp['option_name_already_taken']['title'].from_target(ctx),
                            description=__located_resp['option_name_already_taken']['description'].from_target(ctx).format(name=name),
                            color=Color.red()
                        ).add_field(
                            name=__located_resp['option_name_already_taken']['description_field']['name'].from_target(ctx),
                            value=f'```\n{description}\n```'
                        ),
                        hidden=True
                    )
                data.option_names.append(name)
                data.options.append(NamedDict('Option', {'name': name, 'description': description, 'id': inter.id, 'autor_id': ctx.author.id, 'author': ctx.author}))
                components = [ctx.message.components[0], [
                    SelectMenu(
                        custom_id=f'poll:{data.id}:options',
                        options=[
                            SelectOption(
                               label=o.name,
                               value=str(o.id),
                               description=o.description if o.description else o.name
                            ) for o in data.options
                        ],
                        placeholder=__located_resp['choose_option_placeholder'].from_target(ctx.guild).format(
                            max_choices=min(len(data.options), data.max_choices),
                            choices=len(data.options),
                            min_choices=f' (min. {data.min_choices})' if data.min_choices != 1 else ""
                        ),
                        max_values=min(len(data.options), data.max_choices),
                        min_values=data.min_choices
                    )
                ]]
                await ctx.edit(components=components)
                await inter.respond('Successfully added option. `✅`', hidden=True)

    @commands.Cog.on_click(r'^poll:\d+:add-option$')
    async def poll_add_option(self, ctx: ComponentInteraction, button):
        __located_resp = DATA['button_responses']['poll_create']['add_option']
        data: NamedDict[ModalSuggestions.poll_data_attributes] = self.get_poll(button.custom_id)
        if data.voting_type == 'select menu':
            def build_description(option: NamedDict):
                description = option.description if option.description else option.name
                author = option.author
                if author == data.author:
                    author_str = f' [Poll creator]'
                    if not data.anonymous:
                        author_str += f'({data.author})'
                else:
                    author_str = f' [{option.author}]'
                description += author_str
                return description
            await ctx.respond_with_modal(
                Modal(
                    title=__located_resp['select menu']['title'].from_target(ctx),
                    custom_id=f'poll:add-option:{ctx.id}',
                    components=[
                        TextInput(
                            label=__located_resp['select menu']['fields']['name']['label'].from_target(ctx),
                            custom_id='option-name',
                            placeholder=__located_resp['select menu']['fields']['name']['placeholder'].from_target(ctx),
                            max_length=50,
                            min_length=1,
                        ),
                        TextInput(
                            label=__located_resp['select menu']['fields']['description']['label'].from_target(ctx),
                            custom_id='option-description',
                            placeholder=__located_resp['select menu']['fields']['description'][
                                'placeholder'].from_target(ctx),
                            max_length=(100 - (len(f' [Poll author]' + (
                                f'({ctx.author})' if not data.anonymous else "")) if ctx.author == data.author else len(
                                f' [{ctx.author}]'))),
                            min_length=10,
                            required=False
                        )
                    ]
                )
            )
            try:
                inter: ModalSubmitInteraction = await self.bot.wait_for('modal_submit', check=lambda
                    i: i.custom_id == f'poll:add-option:{ctx.id}', timeout=600)
            except asyncio.TimeoutError:
                return await ctx.channel.send(
                    f'{ctx.author.mention}: Adding of option cancelled because of taking to long.')
            else:
                name = inter.get_field('option-name').value
                description = inter.get_field('option-description').value
                if name in data.option_names:
                    return await inter.respond(
                        embed=discord.Embed(
                            title=__located_resp['option_name_already_taken']['title'].from_target(ctx),
                            description=__located_resp['option_name_already_taken']['description'].from_target(
                                ctx).format(name=name),
                            color=Color.red()
                        ).add_field(
                            name=__located_resp['option_name_already_taken']['description_field']['name'].from_target(
                                ctx),
                            value=f'```\n{description}\n```'
                        ),
                        hidden=True
                    )
                data.option_names.append(name)
                data.options.append(NamedDict('Option', {'name': name, 'description': description, 'id': inter.id,
                                                         'autor_id': ctx.author.id, 'author': ctx.author}))
                components = ctx.message.components.copy()
                components[0] = [
                    SelectMenu(
                        custom_id=f'poll:{data.id}:options',
                        options=[
                            SelectOption(
                                label=o.name,
                                value=str(o.id),
                                description=build_description(o)
                            ) for o in data.options
                        ],
                        placeholder=__located_resp['choose_option_placeholder'].from_target(ctx.guild).format(
                            max_choices=min(len(data.options), data.max_choices),
                            choices=len(data.options),
                            min_choices=f' (min. {data.min_choices})' if data.min_choices != 1 else ""
                        ),
                        max_values=min(len(data.options), data.max_choices),
                        min_values=data.min_choices
                    )
                ]
                await ctx.edit(components=components)
                await inter.respond('Successfully added option. `✅`', hidden=True)

    @commands.Cog.on_click('^poll:create:\d+:start$')
    async def start_poll(self, ctx: ComponentInteraction, button: Button):
        data = self.get_poll(button.custom_id, from_setup=True)
        channel = data.channel
        components = []
        poll_embed = discord.Embed(
            title=data.title,
            color=data.color
        )
        if description:= data.description:
            poll_embed.description = description
        if data.anonymous:
            poll_embed.set_footer(text='This is an anonymous poll.')
        else:
            poll_embed.set_author(name=f'Poll created by {data.author}', url=f'https://discord.com/users/{data.author_id}?guild={ctx.guild_id}', icon_url=ctx.author.display_avatar_url)
        if data.voting_type == 'select menu':
            __located_resp = DATA['button_responses']['poll_create']['add_option']
            def build_description(option: NamedDict):
                description = option.description if option.description else option.name
                author = option.author
                if author == data.author:
                    author_str = f' [Poll creator]'
                    if not data.anonymous:
                        author_str += f'({data.author})'
                else:
                    author_str = f' [{option.author}]'
                description += author_str
                return description

            components.append(
                [
                    SelectMenu(
                        custom_id=f'poll:{data.id}:options',
                        options=[
                            SelectOption(
                                label=o.name,
                                value=str(o.id),
                                description=build_description(o)
                            ) for o in data.options
                        ],
                        placeholder=__located_resp['choose_option_placeholder'].from_target(ctx.guild).format(
                            max_choices=min(len(data.options), data.max_choices),
                            choices=len(data.options),
                            min_choices=f' (min. {data.min_choices})' if data.min_choices != 1 else ""
                        ),
                        max_values=min(len(data.options), data.max_choices),
                        min_values=data.min_choices
                    )
                ]
            )
            if data.users_can_add_options:
                components.append(
                    [
                        Button(
                            label='Add option',
                            custom_id=f'poll:{data.id}:add-option',
                            style=ButtonStyle.blurple,
                            emoji='<:listplus:977234311130517564>'
                        )
                    ]
                )
        data.poll_msg = poll_msg = await channel.send(content=data.ping if data.ping is not None else None, embed=poll_embed, components=components)
        poll_msg: discord.Message = poll_msg

        await ctx.edit(components=[a.disable_all_buttons() for a in ctx.message.components])
        await ctx.respond(f'Successfully started the [poll]({poll_msg.jump_url}) in {channel.mention} ✅.', hidden=True)
        if data.create_discussion_thread:
            data.discussion_thread = await poll_msg.create_thread(name='Discussion', auto_archive_duration=discord.AutoArchiveDuration.one_week)
        self.active_polls[str(data.id)] = data

def setup(bot):
    bot.add_cog(ModalSuggestions(bot))
