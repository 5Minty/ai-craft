import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from models import MinecraftBuild
from langchain_core.output_parsers import JsonOutputParser

# Video about creating a vector DB using lang chain for embeddings
# https://www.youtube.com/watch?v=CK0ExcCWDP4

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class MinecraftCodeGenerator:

    def __init__(self):
        
        """

        Initializes LLM

        """
        self.parser = JsonOutputParser(pydantic_object=MinecraftBuild)
        # format_instructions = self.parser.get_format_instructions()

        system = """You are a bot designed to generate JSON output that conforms to the following schema for building structures in Minecraft.
        Return only JSON output that follows this schema:
        
        Example format:
        {{
            "schematic_name": "small_house",
            "blocks": [
                {{"block_type": "stone", "x": 0, "y": 0, "z": 0}},
                {{"block_type": "stone", "x": 1, "y": 0, "z": 0}},
                {{"block_type": "stone", "x": 2, "y": 0, "z": 0}},
                {{"block_type": "stone", "x": 0, "y": 0, "z": 1}},
                {{"block_type": "stone", "x": 2, "y": 0, "z": 1}},
                {{"block_type": "stone", "x": 0, "y": 0, "z": 2}},
                {{"block_type": "stone", "x": 1, "y": 0, "z": 2}},
                {{"block_type": "stone", "x": 2, "y": 0, "z": 2}},
                {{"block_type": "oak_planks", "x": 1, "y": 1, "z": 1}},
                {{"block_type": "oak_planks", "x": 1, "y": 2, "z": 1}},
                {{"block_type": "stone", "x": 0, "y": 1, "z": 0}},
                {{"block_type": "stone", "x": 2, "y": 1, "z": 0}},
                {{"block_type": "stone", "x": 0, "y": 1, "z": 2}},
                {{"block_type": "stone", "x": 2, "y": 1, "z": 2}},
                {{"block_type": "stone", "x": 0, "y": 2, "z": 0}},
                {{"block_type": "stone", "x": 2, "y": 2, "z": 0}},
                {{"block_type": "stone", "x": 0, "y": 2, "z": 2}},
                {{"block_type": "stone", "x": 2, "y": 2, "z": 2}},
                {{"block_type": "air", "x": 1, "y": 1, "z": 0}}
                ]
        }}
        
        IMPORTANT: Always return valid JSON that matches this schema exactly.
        Do not include any explanation text, only return the JSON object.
        """

        # system_prompt = system.format(format_instructions=format_instructions)
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        self.prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
        self.few_shot_llm = self.prompt | self.llm | self.parser

    def generate_code(self, message):

        """

        Sends a message to the LLM and returns its response.

        :param message: The message to be sent

        :return: The LLM's response

        """
        try:
            completion = self.few_shot_llm.invoke({"input": message})

            print(completion)

            if isinstance(completion, MinecraftBuild):
                return completion.model_dump_json()
            
            if isinstance(completion, dict):
                build = MinecraftBuild(**completion)
                return build.model_dump_json()
        except Exception as e:
            print(f"An error occurred: {e}")
            default_build = MinecraftBuild(
                schematic_name="error_fallback",
                blocks=[
                    {"block_type": "stone", "x": 0, "y": 0, "z": 0},
                ]
            )
            return default_build.model_dump_json()
