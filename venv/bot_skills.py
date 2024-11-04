from models import MinecraftBuild

def place_block(bot, block_type, x, y, z, direction=False):
    valid_directions = {"north", "south", "east", "west"}
    
    # Format the command and send it using bot.chat instead of print
    if direction in valid_directions:
        command = f"/setblock {x} {y} {z} {block_type}[facing={direction}]"
    else:
        command = f"/setblock {x} {y} {z} {block_type}"
    
    bot.chat(command)

def build_from_json(bot, json_data, isPath=False):
    # with open(file, 'r') as file:
    #     json_data = file.read()
    pos = bot.entity.position
    base_x = int(pos.x)
    base_y = int(pos.y)
    base_z = int(pos.z)
    # Parse the JSON data into a MinecraftBuild instance
    minecraft_build = MinecraftBuild.model_validate_json(json_data) # class that parses and holds json using BaseModel 
    for block in minecraft_build.blocks:
        place_block(bot, block.block_type, block.x + base_x, block.y + base_y, block.z + base_z, getattr(block, 'direction', False))


def build_shack(bot, direction):
    # Get the bot's current position
    pos = bot.entity.position
    base_x = int(pos.x)
    base_y = int(pos.y)
    base_z = int(pos.z)

    width = 5
    height = 3
    depth = 5

    WOOD = "minecraft:stone"
    DOOR = "minecraft:oak_door"
    GLASS = "minecraft:glass"

    # Build the floor
    for x in range(width):
        for z in range(depth):
            place_block(bot, WOOD, base_x + x, base_y, base_z + z)

    # Build the walls (leave space for the door and windows)
    for y in range(1, height):
        for x in range(width):
            for z in range(depth):
                if x == 0 or x == width - 1 or z == 0 or z == depth - 1:
                    if not (y == 1 and x == width // 2 and z == 0):
                        if not (y == 2 and (x == 1 or x == 3) and z == depth - 1):
                            place_block(bot, WOOD, base_x + x, base_y + y, base_z + z)

    # Add the door
    place_block(bot, DOOR, base_x + width // 2, base_y + 1, base_z, direction=direction)
    place_block(bot, DOOR, base_x + width // 2, base_y + 2, base_z, direction=direction)

    # Add the windows
    place_block(bot, GLASS, base_x + 1, base_y + 2, base_z + depth - 1)
    place_block(bot, GLASS, base_x + 3, base_y + 2, base_z + depth - 1)

    # Build the roof
    for x in range(width):
        for z in range(depth):
            place_block(bot, WOOD, base_x + x, base_y + height, base_z + z)

    # Send a reload command if needed
    # bot.chat("/reload")