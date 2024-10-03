from javascript import require, On
import sys
from dotenv import load_dotenv

import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

mineflayer = require('mineflayer')

class BuilderBot:

    def init(self):

        """

        Initializes a bot in minecraft

        """
        try:
            host = '35.23.178.32'
            port = 54569
            username = "R2D2"  # Replace with the desired bot username
            self.bot = mineflayer.createBot({
                "host": host,
                "port": port,
                "username": username,
            })
            self.setup_listeners()
        except Exception as e:
            print(f'failed to start bot')
            return


    def setup_listeners(self):

        @On(self.bot, 'spawn')
        def handle_spawn(*args):

            """

            Spawns the bot next to you (need player coords)

            """
            playerFilter = lambda entity: entity.type == 'player'
            player = self.bot.nearestEntity(playerFilter)
            if player:
                pos = player.position
                self.bot.chat(f"/tp AustinMinty")
            else:
                self.bot.chat("No player nearby to teleport to!")

        @On(self.bot, 'chat')
        def on_chat(this, sender, message, *args):

            """

            Handles chats :param sender: The sender of the message :param message: The message that got sent

            """

            if message.lower() == 'come':
                playerFilter = lambda entity: entity.type == 'player'
                player = self.bot.nearestEntity(playerFilter)
                if player:
                    pos = player.position
                    self.bot.chat(f"/tp AustinMinty")
                    # Move bot to the player's location (example method, adapt as necessary)
                    # self.bot.navigate.to(pos), self.bot.moveTo
                else:
                    self.bot.chat(f"I cannot come")
            else:
                response = self.get_openai_response(message)
                if response:
                    self.bot.chat(response)

        @On(self.bot, 'end')
        def on_end(*args):

            """

            Ends the bot

            """
            # TODO: say a message when leaving or app ending
            print("Bot disconnected.")