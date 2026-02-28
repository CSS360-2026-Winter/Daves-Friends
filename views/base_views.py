"""
Provides a base view for a the bot.
"""

import random

from discord import Colour
import discord


class BaseViews:
    """
    The base view for the bot which is extended by the particular views. Provides all the basic
    functions that can be reused elsewhere. Contains cool gifs, pretty colors, and a footer.
    """

    def __init__(self):
        self._pretty_colors = [
            0xD69CBC,
            0x51074A,
            0xFF007F,
            0x40E0E0,
            0x98FF98,
            0xFFF44F,
            0xCDFFDB,
            0xCFAFDD,
            0xB9CEFB,
            0xFFB8EA,
            0xB4BE89,
            0xCB736E,
            0xFE7E0F,
            0xFAEBD7,
            0x008080,
        ]
        # pylint: disable=line-too-long
        self._cool_gifs = [
            "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjVoYXFxM3g2ZWRsaDYyOHozOW53MTYxd2J6MmtrejhnNm1vNG90dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wrmVCNbpOyqgJ9zQTn/giphy.gif",
            "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExajFhZTQwaWpoN3E5dTltYmxsZGF6bXJ0Y2tuYXhmNGhuYTl0ajZtZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1351TySLYhyXII/giphy.gif",
            "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGJpcWs1OWdvZWIxbzIyMnpyZDJrM2cwY3ozOGgzaTF4N25sd2Z3dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KbdF8DCgaoIVC8BHTK/giphy.gif",
        ]
        self._error_color = Colour(0xD21F3C)
        self._footer = "Uno Discord Bot • Class Project for UWB 360"

    def get_random_color(self) -> Colour:
        """
        Gets a random color from the list of pretty colors.
        """
        return Colour(random.choice(self._pretty_colors))

    def get_random_gif(self) -> str:
        """
        Gets a random GIF from the list of cool GIFs.
        """
        return random.choice(self._cool_gifs)

    def update_embed(self, title: str, desc: str, gif=True) -> discord.Embed:
        """
        Provides the framework for a Discord embed that displays an update.
        """
        return self._build_embed(
            "UPDATE: " + title,
            desc=desc,
            color=self.get_random_color(),
            gif=gif,
            time_stamp=True,
        )

    def error_embed(self, title: str, desc: str, gif=True) -> discord.Embed:
        """
        Provides the framework for a Discord embed that displays an error.
        """
        return self._build_embed("ERROR: " + title, desc, self._error_color, gif)

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def _build_embed(
        self,
        title: str,
        desc: str,
        color: Colour,
        gif: bool = True,
        footer: bool = True,
        time_stamp: bool = True,
        random_gif: bool = False,
        author: discord.User = None,
    ) -> discord.Embed:

        embed = discord.Embed(
            title=title,
            description=desc,
            colour=color,
        )

        if gif:
            embed.set_image(url=self.get_random_gif())

        if footer:
            embed.set_footer(text=self._footer)

        if time_stamp:
            embed.timestamp = discord.utils.utcnow()

        if random_gif:
            embed.set_image(url=self.get_random_gif())

        if author:
            embed.set_author(name=author.name, icon_url=author.display_avatar.url)

        return embed
