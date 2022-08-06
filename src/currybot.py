from http import client
from bookembed import BookEmbed, EmbedField
from converter import CurrencyConverter
import discord

from typing import Any, TypeVar

UALPHABET = [ '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', 
              '🇺', '🇻', '🇼', '🇽', '🇾', '🇿' ]

def emoji_flag(text: str):
    text = text.lower()
    return ''.join([UALPHABET[ord(i) - ord('a')] for i in text])

#T = TypeVar("T")
def try_convert_to_float(a: Any) -> float: # Try convert value to floating point.
    try: return float(a)
    except: return None

class CurryBot(discord.Client):
    def __init__(self, currency_apikey: str, *, loop=None, **options):
        super().__init__(loop=loop, **options)

        self.converter = CurrencyConverter(currency_apikey)
        self.currencies_pages = []

        self.error_embed      = discord.Embed(title="Error", colour=0xff2c00)
        self.convertion_embed = discord.Embed(title="Convertion", colour=0x00e3b6)
        self.__update_currencies_embed()

        self.help_embed = discord.Embed(title="Help", colour=0xf0c500, description="Available commands.")
        self.help_embed.add_field(name='list', value='Lists the available currencies. ```!list```', inline=False)
        self.help_embed.add_field(name='convert', value='Converts ammount from one currency unit to another.\
        ```!convert {AMMOUNT} from {INPUT_CURRENCY} to {OUTPUT_CURRENCY}```', inline=False)

    def __update_currencies_embed(self) -> None:
        cntrys = self.converter.list_countries()
        codes = self.converter.list_currencies()
        flags = [emoji_flag(code[:-1]) for code in codes]

        names_field = EmbedField(name="Name", inline=True)
        codes_field = EmbedField(name="Code", inline=True)
        flags_field = EmbedField(name="Flag", inline=True)

        ITEMS_PER_PAGE = 10

        currencies_pages = []

        for i in range(len(cntrys)):
            if i != 0 and i % ITEMS_PER_PAGE == 0:
                currencies_pages.append({ "fields": [flags_field.to_dict(),\
                    names_field.to_dict(),codes_field.to_dict()] })

                flags_field.value = ""
                codes_field.value = ""
                names_field.value = ""

            flags_field.value += flags[i] + '\n'
            codes_field.value += codes[i] + '\n'
            names_field.value += cntrys[i] + '\n'
            
        if len(cntrys) % ITEMS_PER_PAGE > 0:
            self.currencies_pages.append({ "fields": [flags_field.to_dict(),\
                names_field.to_dict(),codes_field.to_dict()] })

        self.currencies_book = BookEmbed(currencies_pages, title="Currencies", 
                                         colour=0x00e3b6, description="Available currencies.")

    async def __send_error(self, msg: str, message: discord.Message) -> None:
        self.error_embed.description = msg
        await message.channel.send(embed=self.error_embed)

    async def __send_convertion(self, ammount: float, from_cntry: str, to_cntry: str, 
                                message: discord.Message) -> bool:
        converted_ammount = self.converter.convert(ammount, from_cntry, to_cntry)
        if converted_ammount == None:
            return False
        
        self.convertion_embed.description = "{} {:,.2f} **{}**⤵️\n{} {:,.2f} **{}**"\
            .format(emoji_flag(from_cntry[:-1]), ammount, from_cntry, emoji_flag(to_cntry[:-1]),\
            converted_ammount, to_cntry)

        await message.channel.send(embed=self.convertion_embed)
        return True
    
    async def __send_help(self, message: discord.Message) -> None:
        await message.channel.send(embed=self.help_embed)

    async def on_ready(self):
        print("{0} is online.".format(self.user))

    async def on_message(self, message):
        if message.author != self.user: # Don't do processing on own messages
            if message.content[0] == '!': # All commands start with the control character '!'
                keywords = message.content[1:].split(' ')
                
                command = keywords[0]
                args = keywords[1:]

                if command == "list": # Currency listing command
                    if self.converter.try_update_currencies():
                        self.__update_currencies_embed()
                    await self.currencies_book.send(message.channel, message.author.id)
                    pass

                elif command == 'convert': # Currency convertion command
                    if len(args) > 0:
                        ammount = try_convert_to_float(args[0])
                        if ammount != None:
                            if args[1] == 'from':
                                from_cntry = args[2]
                                if args[3] == 'to':
                                    to_cntry = args[4]
                                    self.converter.try_update_convertions()
                                    success = await self.__send_convertion(ammount, from_cntry, to_cntry, message)
                                    if success == False: # Err: invalid currency code
                                        await self.__send_error("invalid currency code.", message)
                                else: # Err: expected keyword "to"
                                    await self.__send_error("Expected keyword \"to\".", message)
                            else: # Err: expected keyword "from"
                                await self.__send_error("Expected keyword \"from\".", message)
                        else: # Err: Arg was not a number
                            await self.__send_error("Invalid ammount.", message)
                    else: # Err: No arguments were added
                        await self.__send_error("Expected arguments.", message)
                
                elif command == 'help':
                    await self.__send_help(message)
                    pass

                else: # Unknown command
                    await self.__send_error("Unknown command. Use `!help` to display the command list.", message)

            

    async def on_raw_reaction_add(self, payload):
        if self.user.id != payload.user_id:
            await self.currencies_book.reaction_event(payload)

    async def on_raw_reaction_remove(self, payload):
        if self.user.id != payload.user_id:
            await self.currencies_book.reaction_event(payload)
