def place_block(block_type, x, y, z, direction=False):
    valid_directions = {"north", "south", "east", "west"}
    
    if direction in valid_directions:
        print(f"setblock {x} {y} {z} {block_type}[facing={direction}]")
    else:
        print(f"setblock {x} {y} {z} {block_type}")


def build_shack(base_x, base_y, base_z, direction):
    width = 5
    height = 3
    depth = 5
    
    WOOD = "minecraft:stone"
    DOOR = "minecraft:oak_door"
    GLASS = "minecraft:glass"
    
    # Build the floor
    for x in range(width):
        for z in range(depth):
            place_block(WOOD, base_x + x, base_y, base_z + z)

    # Build the walls (leave space for the door and windows)
    for y in range(1, height):
        for x in range(width):
            for z in range(depth):
                if x == 0 or x == width - 1 or z == 0 or z == depth - 1:
                    # Leave space for the door (middle of the front wall)
                    if not (y == 1 and x == width // 2 and z == 0):
                        # Leave space for the windows
                        if not (y == 2 and (x == 1 or x == 3) and z == depth - 1):
                            place_block(WOOD, base_x + x, base_y + y, base_z + z)

    # Add the door (two blocks high)
    place_block(DOOR, base_x + width // 2, base_y + 1, base_z, direction=direction)
    place_block(DOOR, base_x + width // 2, base_y + 2, base_z, direction=direction)

    # Add the windows (two windows in the back wall)
    place_block(GLASS, base_x + 1, base_y + 2, base_z + depth - 1)
    place_block(GLASS, base_x + 3, base_y + 2, base_z + depth - 1)

    # Build the roof
    for x in range(width):
        for z in range(depth):
            place_block(WOOD, base_x + x, base_y + height, base_z + z)

    print(f"reload")
