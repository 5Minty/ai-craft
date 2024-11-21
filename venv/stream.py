import json

class StreamCallback:
    def __init__(self, parser):
        """
        Initializes the callback with an empty buffer and a parser for validation.
        :param parser: A JSON parser to validate against the MinecraftBuild schema.
        """
        self.parser = parser
        self.current_data = ""
        self.complete_data = []

    def handle_chunk(self, chunk):
        """
        Processes a streamed chunk of data.
        :param chunk: A chunk of JSON data.
        """
        try:
            # Attempt to serialize chunk if it's not already JSON-compatible
            if not isinstance(chunk, (str, dict)):
                chunk = json.loads(json.dumps(chunk, default=self.custom_serializer))  # Serialize non-standard objects

            # Process the chunk as JSON
            self.current_data += json.dumps(chunk)
            parsed = json.loads(self.current_data)

            # Validate against MinecraftBuild schema
            if "schematic_name" in parsed and "blocks" in parsed:
                validated_data = self.parser.parse_obj(parsed)
                self.complete_data.append(validated_data.dict())
                self.current_data = ""
        except json.JSONDecodeError:
            # If incomplete JSON, continue buffering
            pass
        except Exception as e:
            print(f"Validation error in chunk: {e}")

    def custom_serializer(self, obj):
        """
        Custom serializer for non-JSON-serializable objects.
        """
        if hasattr(obj, "__dict__"):
            return obj.__dict__  # Serialize custom objects as dictionaries
        return str(obj)  # Fallback to string representation

    def get_full_json(self):
        """
        Combines all validated parts into a single JSON structure.
        :return: A merged JSON object adhering to the MinecraftBuild schema.
        """
        return {
            "schematic_name": "streamed_build",
            "blocks": [block for part in self.complete_data for block in part.get("blocks", [])]
        }
