from javascript import require, On
import sys
from dotenv import load_dotenv
import requests
from openai import OpenAI
client = OpenAI() # uses the api_key to create a client object
from bot_skills import build_shack

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
            host = '35.23.120.33'
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
            self.bot.chat(f"/tp AustinMinty") # TODO: don't hard code this

        @On(self.bot, 'chat')
        def on_chat(this, sender, message, *args):

            """

            Handles chats :param sender: The sender of the message :param message: The message that got sent

            """
            if sender == self.bot.username:
                return

            if message.lower() == 'come':
                self.bot.chat(f"/tp AustinMinty") # TODO: don't hard code this
            elif message.lower() == 'leave':
                self.bot.chat(f"byeee")
                # TODO: delete bot
            elif message.lower() == 'build shack':
                build_shack(self.bot, 'west')
            elif message.startswith('/'):
                return
            else:
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert builder in Minecraft that answers concisely and always responds to me as Sammy Wammy."},
                        {
                            "role": "user",
                            "content": message
                        },
                        
                    ],
                    max_tokens=128
                )

                print(completion.choices[0].message)
                self.bot.chat(completion.choices[0].message.content)

        @On(self.bot, 'end')
        def on_end(*args):

            """

            Ends the bot

            """
            print("Bot disconnected.")