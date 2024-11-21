import os
import ast
import json
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from dotenv import load_dotenv
from models import MinecraftBuild
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
import tiktoken
from collections import defaultdict
from bot_skills import build_from_json
from stream import StreamCallback

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class MinecraftCodeGenerator:
    id_key = 'doc_id'
    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=MinecraftBuild)

        system = """You are a bot designed to generate highly detailed and complex JSON output for building large and intricate structures in Minecraft, following the provided schema and examples.

        **JSON Output Requirements:**
        Return raw JSON with this schema:

        {{
            "schematic_name": string,
            "blocks": [
                {{"block_type": string, "x": integer, "y": integer, "z": integer}},
                ...
            ]
        }}

        - Only raw JSON, no markdown or code block syntax.
        """

        with open('few_shot.txt', 'r') as file:
            self.few_shot = file.read()

        self.llm = ChatOpenAI(model="gpt-4o", request_timeout=300, temperature=0.8, streaming=True)
        self.encoding = tiktoken.encoding_for_model("gpt-4o")
        self.prompt = ChatPromptTemplate.from_messages([("system", system), 
            HumanMessagePromptTemplate.from_template("""
        {input}

        **Refer to these detailed schematics to generate a highly detailed and intricate build:**

        {context}

        **Instructions:**
        - Ensure block counts align with schema.
        - Use only valid Minecraft block IDs (e.g., "stone_bricks", "oak_planks").
        - Please add decorative blocks like flowers, lighting, and doors.
        - Ensure walls and roofs are completely filled in with no air.
        - Determine facing directions for orientable blocks based on the bots fixed position.

        **Constraints:**
        - Block counts at 100 are capped but may represent larger totals.
        - Use up to the maximum token limit.
        - Only return RAW JSON, no comments or markdown.
        """)])
            
        self._initialize_retriever()    
        
        if self.retriever:
            question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
            self.rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)

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

        doc_ids = [str(uuid.uuid4()) for _ in docs]

        summary_docs = [
            Document(page_content=summaries[i], metadata={self.id_key: doc_ids[i], 'full_content': docs[i].page_content})
            for i in range(len(summaries))
        ]

        for doc in summary_docs[:5]:
            print(doc.page_content)

        if summary_docs:
            self.vectorstore = Chroma.from_documents(
                documents=summary_docs, 
                embedding=OpenAIEmbeddings()
            )

            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity", 
                search_kwargs={"k": 3}
            )
        else:
            raise ValueError("No documents loaded")

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

    def generate_code(self, message, botPosition):
        try:
            # TODO: callback = StreamCallback(self.parser)

            retrieved_docs = self.retriever.invoke(message)

            for doc in retrieved_docs:
                if doc.page_content.lower() in message.lower():
                    json_data = doc.metadata.get('full_content', doc.page_content)
                    print(f"Exact match found for {doc.page_content}. Building directly from JSON data.")
                    if isinstance(json_data, str):
                        json_data = json.dumps(ast.literal_eval(json_data))
                        parsed_data = json.loads(json_data)

                        formatted_data = {
                            "schematic_name": doc.page_content,
                            "blocks": parsed_data
                        }

                        print(formatted_data)
                        if 'blocks' in formatted_data and 'schematic_name' in formatted_data:
                            build = MinecraftBuild(**formatted_data)
                            return build.model_dump_json()
                        else:
                            raise ValueError("JSON data does not match the expected schema.")

            combined_docs = []

            for i, doc in enumerate(retrieved_docs):
                schematic_name = doc.page_content
                context = doc.metadata.get('full_content', doc.page_content)

                python_dict = ast.literal_eval(context)
                valid_json_string = json.dumps(python_dict)
                blocks = json.loads(valid_json_string)

                compressed_context = self.compress_blocks(blocks)

                # Only summarize blocks for all but the first document
                if i > 0:
                    summarized = self.summarize_blocks(compressed_context, schematic_name)
                    combined_docs.extend(summarized)
                else:
                    combined_docs.append({
                        "schematic_name": schematic_name,
                        "blocks": compressed_context
                    })

            combined_docs_json = json.dumps(combined_docs)

            # summarized_docs_json = json.dumps(summarized_docs)

            final_prompt = self.prompt.format(input=message, context=combined_docs_json) + f"\n**Bot's Current Position:** {botPosition['x']}, {botPosition['y']}, {botPosition['z']}\n"
            num_tokens = len(self.encoding.encode(final_prompt))
            print("Final Prompt:\n", final_prompt)
            print(f"Total tokens in prompt: {num_tokens}")

            # TODO: for chunk in self.rag_chain.stream({"input": message, "context": summarized_docs_json}):
            #     callback.handle_chunk(chunk)

            completion = self.rag_chain.invoke({
                "input": message,
                "context": combined_docs_json
            })

            num_tokens = len(self.encoding.encode(completion['answer']))
            print("Completion keys:", completion["answer"])
            print(f"Total tokens in response: {num_tokens}")

            # TODO: final_json = callback.get_full_json()
            # return json.dumps(final_json, indent=2)

            answer_text = completion["answer"]
            answer_text = answer_text.replace('```json', '').replace('```', '').strip()

            answer_dict = json.loads(answer_text)

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
        
    def compress_blocks(self, blocks, max_count=100):
        grouped = defaultdict(list)
        for block in blocks:
            grouped[block["block_type"]].append((block["x"], block["y"], block["z"]))
        
        compressed = []
        for block_type, coords in grouped.items():
            if len(coords) > max_count:
                coords = coords[:max_count]
            compressed.append({
                "block_type": block_type,
                "coordinates": coords
            })
        return compressed
    
    def summarize_blocks(self, blocks, schematic_name):
        summarized = []
        
        for block in blocks:
            block_type = block["block_type"]
            coordinates = block["coordinates"]
            block_count = len(coordinates)
            
            if block_count >= 5:
                # direction = None
                # if "stairs" in block_type or "door" in block_type or "trapdoor" in block_type: # TODO: make container of orientable blocks
                #     direction = self.determine_orientation_toward_open_space(
                #         coordinates[0][0],  # x
                #         coordinates[0][1],  # y
                #         coordinates[0][2],  # z
                #         blocks  # all blocks in the schematic
                #     )

                summarized.append({
                    "schematic_name": schematic_name,
                    "block_type": block_type,
                    "block_count": block_count,
                    # "direction": direction
                })
        
        return summarized

    def determine_orientation_toward_open_space(self, x, y, z, all_blocks):
        neighbors = {
            "north": (x, y, z - 1),
            "south": (x, y, z + 1),
            "east": (x + 1, y, z),
            "west": (x - 1, y, z)
        }
        for direction, coord in neighbors.items():
            if coord not in [b["coordinates"] for b in all_blocks]:
                return direction
        return "north"


