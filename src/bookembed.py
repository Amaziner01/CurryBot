from typing import Dict, List
from discord import RawReactionActionEvent, TextChannel, Embed

class EmbedField:
    def __init__(self, *, name: str="", value: str="", inline: bool="") -> None:
        self.name = name
        self.value = value
        self.inline = inline

    def clear(self) -> None:
        self.name = ""
        self.value = ""
        self.inline = False

    def __str__(self) -> str:
        return "EmbedField: name=\"{0}\"; value=\"{1}\"; inline={2}"\
                .format(self.name, self.value, self.inline)
    pass

    def to_dict(self) -> dict:
        return { "name": self.name, "value": self.value, "inline": self.inline }

DiscordBookPage = Dict[str, dict]

class BookEmbed:
    def __init__(self, pages: List[DiscordBookPage], *, title: str="", colour: int=0, description: str="") -> None:
        self.page_count = len(pages)
        self.user_instances = {}
        self.pages = pages
        self.embed = Embed(title=title, colour=colour, description=description)

    def __set_page(self, page_index: int) -> None:
        self.embed.clear_fields()
        page = self.pages[page_index]

        if "fields" in page:
            for field in page["fields"]:
                self.embed.add_field(name=field["name"], value=field["value"],\
                                     inline=field["inline"])
        
        if "description" in page:
            self.embed.description = page["description"]

        self.embed.set_footer(text="{0}/{1}".format(page_index + 1, self.page_count))

    def reset(self) -> None:
        self.current_page = 0
        self.embed.clear_fields()
        self.__set_page(0)
        self.embed.set_footer(text="1/{0}".format(self.page_count))

    async def send(self, channel: TextChannel, user_id: int) -> None:
        self.__set_page(0)

        msg = await channel.send(embed=self.embed)
        await msg.add_reaction('⬅️')
        await msg.add_reaction('➡️')

        data = { "message": msg, "current_page": 0}
        msg = self.user_instances[user_id] = data

    async def __next_page(self, user_id: int) -> None:
        data = self.user_instances[user_id]

        current = data["current_page"]
        msg = data["message"]

        if current < self.page_count - 1:
            current += 1
            self.__set_page(current)
            await msg.edit(embed=self.embed)
            current = data["current_page"] = current

    async def __previous_page(self, user_id: int) -> None:
        data = self.user_instances[user_id]

        current = data["current_page"]
        msg = data["message"]

        if current > 0:
            current -= 1
            self.__set_page(current)
            await msg.edit(embed=self.embed)
            current = data["current_page"] = current

    async def reaction_event(self, payload: RawReactionActionEvent):
        if payload.user_id in self.user_instances:
            msg = self.user_instances[payload.user_id]["message"]
            if payload.message_id == msg.id:
                if str(payload.emoji) == '⬅️':
                    await self.__previous_page(payload.user_id)

                elif str(payload.emoji) == '➡️':
                    await self.__next_page(payload.user_id)
