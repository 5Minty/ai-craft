import os
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

# Video about creating a vector DB using lang chain for embeddings
# https://www.youtube.com/watch?v=CK0ExcCWDP4

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class MinecraftCodeGenerator:
    id_key = 'doc_id' # TODO: should this be a constant??
    def __init__(self):
        
        """

        Initializes LLM

        """
        self.parser = JsonOutputParser(pydantic_object=MinecraftBuild)
        # format_instructions = self.parser.get_format_instructions()

        system = """You are a bot designed to generate JSON output based on the following schema for building structures in Minecraft and based on provided schema examples.
        When generating a build, you should:
        1. Analyze the block patterns and structure from the provided example schematics
        2. Maintain similar complexity and scale as the examples (use the same number of blocks)
        3. Use similar block types and arrangements
        4. Preserve architectural features present in the examples
        
        Return only JSON output that follows this schema:
        {{
            "schematic_name": string,
            "blocks": [
                {{"block_type": string, "x": integer, "y": integer, "z": integer}},
                ...
            ]
        }}
        
        Important guidelines:
        - Maintain the scale and complexity of the reference schematics
        - Use similar block variety and patterns as shown in the examples
        - Keep architectural features consistent with the building type
        - Ensure structural integrity and completeness
        - Include all necessary blocks for a complete structure
        - Return ONLY the raw JSON with no markdown formatting or code block syntax
        """

        # system_prompt = system.format(format_instructions=format_instructions)
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
        self.prompt = ChatPromptTemplate.from_messages([("system", system), 
            HumanMessagePromptTemplate.from_template("""
        {input}

        Use these example schematics as reference to generate a detailed build plan:
        {context}

        Important:
        - Match the complexity level of the examples
        - Use similar block patterns and arrangements
        - Maintain architectural features shown in the examples
        - Ensure the structure is complete and properly scaled

        Return only JSON format with 'schematic_name' and 'blocks' fields.
        """)])
        # self.few_shot_llm = self.prompt | self.llm | self.parser
            
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

        doc_ids = [str(uuid.uuid4()) for _ in docs] # Each doc should receive an id

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

            # self.vectorstore.docstore.mset(list(zip(doc_ids, docs)))

            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity", 
                search_kwargs={"k": 1}
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

            # completion = self.rag_chain.invoke({"input": message})
            retrieved_docs = self.retriever.invoke(message)
            for i, doc in enumerate(retrieved_docs):
                print(f"Retrieved Doc {i+1}: {doc.page_content}")

            context = "\n".join([doc.metadata.get('full_content', doc.page_content) for doc in retrieved_docs])
            print('context', context[:1000])

            # max_context_length = 3000
            # if len(context) > max_context_length:
            #     print(f"Context is too large ({len(context)} characters). Truncating...")
            #     context = context[:max_context_length]

            completion = self.rag_chain.invoke({
                "input": message,
                "context": context
            })

            print("Completion keys:", completion["answer"])

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
