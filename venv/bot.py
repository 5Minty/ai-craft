from typing import List
from javascript import require, On
from dotenv import load_dotenv
from openai import OpenAI
client = OpenAI() # uses the api_key to create a client object
from bot_skills import build_shack, place_block, build_from_json
from llm import MinecraftCodeGenerator
import json

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
            host = '35.23.45.22' # TODO: way to call ipconfig and get IPv4?
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
            self.codeGen = MinecraftCodeGenerator()

        @On(self.bot, 'chat')
        def on_chat(this, sender, message, *args):

            """

            Handles chats :param sender: The sender of the message :param message: The message that got sent

            """
            if sender == self.bot.username:
                return

            message = str(message)
            
            if message.lower() == 'come':
                self.bot.chat(f"/tp AustinMinty") # TODO: don't hard code this
            elif message.lower() == 'leave':
                self.bot.chat(f"byeee")
                # TODO: delete bot
            elif message.lower() == 'build shack':
                build_shack(self.bot, 'west')
            elif message.lower() == 'build chapel':
                self.bot.chat('schematics')
                build_from_json(self.bot, '../filtered_schematics_json-10.24/filtered_schematics_json/2.json') # TODO: add a param to tell function if file needs to be read or not
            elif message.startswith("build"):
                self.bot.chat('code_generator')
                response = self.codeGen.generate_code(message)
                try:
                    build_from_json(self.bot, response)
                
                except json.JSONDecodeError as json_err:
                    print(f"Error parsing JSON: {json_err}")
                except Exception as e:
                    print(f"Error executing the code: {e}")
            elif message.startswith('/'):
                return
            else:
                self.bot.chat("What do you want from me??")

        @On(self.bot, 'end')
        def on_end(*args):

            """

            Ends the bot

            """
            print("Bot disconnected.")