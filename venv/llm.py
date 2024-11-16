import os
import json
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from models import MinecraftBuild
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document

# Video about creating a vector DB using lang chain for embeddings
# https://www.youtube.com/watch?v=CK0ExcCWDP4

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class MinecraftCodeGenerator:
    id_key = 'document_id' # TODO: should this be a constant??
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
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
        self.prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{context}")])
        # self.few_shot_llm = self.prompt | self.llm | self.parser
            
        self._initialize_retriever()
        
        if self.retriever:
            question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
            self.rag_chain = create_retrieval_chain(self.retriever, question_answer_chain) # TODO: rag_chain not being init'd correctly

    def _initialize_retriever(self):
        summaries = self.get_schematic_names('../filtered_schematics_json-10.24/filtered_schematics_json')
        loader = DirectoryLoader(
            '../filtered_schematics_json-10.24/filtered_schematics_json',
            loader_cls=JSONLoader,
            loader_kwargs={
                'jq_schema': '.blocks',
                'text_content': False
            }
        )
        docs = loader.load()

        doc_ids = [str(uuid.uuid4()) for _ in docs] # Each doc should receive an id

        summary_docs = [
            Document(page_content=s, metadata={self.id_key: doc_ids[i]})
            for i, s in enumerate(summaries)
        ]

        if summary_docs:
            self.vectorstore = Chroma.from_documents(
                documents=summary_docs, 
                embedding=OpenAIEmbeddings()
            )

            # self.vectorstore.docstore.mset(list(zip(doc_ids, docs)))

            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity", 
                search_kwargs={"k": 6}
            )
        else:
            raise ValueError("No documents loaded")
            # TODO: invoke retreiver to see if it finds the right docs - "How do I build a chapel"
            # self.retriever.docstore.mset(list(zip(doc_ids, docs)))

    def get_schematic_names(self, directory):
        schematic_names = []
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                schematic_name = data.get('schematic_name')

                if schematic_name:
                    schematic_names.append(schematic_name)
        return schematic_names

    def generate_code(self, message):

        """

        Sends a message to the LLM and returns its response.

        :param message: The message to be sent

        :return: The LLM's response

        """
        try:
            completion = self.rag_chain.invoke({"input": message})

            print("completion", completion["answer"])

            answer_dict = json.loads(completion["answer"]) # TODO: should I be loading the JSON from the completion?

            if 'schematic_name' in answer_dict and 'blocks' in answer_dict:
                build = MinecraftBuild(**answer_dict)
                return build.model_dump_json()
            else:
                raise ValueError("Missing required fields in the response.")
        except Exception as e:
            print(f"An error occurred: {e}")
            default_build = MinecraftBuild(
                schematic_name="error_fallback",
                blocks=[
                    {"block_type": "stone", "x": 0, "y": 0, "z": 0},
                ]
            )
            return default_build.model_dump_json()
