from typing import List, Optional
from pydantic import BaseModel, Field

class Block(BaseModel):
    block_type: str = Field(description="Type of the block")
    x: int = Field(description="X coordinate of the block")
    y: int = Field(description="Y coordinate of the block")
    z: int = Field(description="Z coordinate of the block")
    facing: Optional[str] = Field(default=None, description="Facing direction of the block")

class MinecraftBuild(BaseModel):
    schematic_name: str = Field(description="Name of the schematic")
    blocks: List[Block] = Field(description="List of blocks in the schematic")