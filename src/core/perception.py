"""
perception.py: Extrae contexto del mundo (inventario, bloques, chat, vida).
"""

def get_bot_status(bot):
    """
    Retorna un diccionario con el estado básico del bot.
    """
    if not bot or not bot.entity:
        return {"error": "El bot no ha spawneado completamente aún."}
        
    position = bot.entity.position
    status = {
        "health": bot.health,
        "food": bot.food,
        "position": {
            "x": round(position.x, 2),
            "y": round(position.y, 2),
            "z": round(position.z, 2)
        },
        "timeOfDay": bot.time.timeOfDay
    }
    return status

def get_inventory(bot):
    """
    Retorna una lista de los items en el inventario del bot.
    """
    if not bot or not bot.inventory:
        return []
        
    items = []
    for item in bot.inventory.items():
        if item:
            items.append({
                "name": item.name,
                "count": item.count,
                "slot": item.slot
            })
    return items

def get_nearby_blocks(bot, radius=3):
    """
    Encuentra bloques no-aire alrededor del bot en un radio específico.
    """
    if not bot or not bot.entity:
        return []

    blocks = []
    # Usar la API de mineflayer findBlocks
    # Esto es una operación básica; para algo más avanzado se requiere iterar en 3D
    try:
        # findBlocks devuelve un array de posiciones
        block_positions = bot.findBlocks({
            "matching": lambda block: block.name != 'air' and block.name != 'cave_air',
            "maxDistance": radius,
            "count": 20
        })
        
        for pos in block_positions:
            block = bot.blockAt(pos)
            if block and block.name != 'air':
                blocks.append({
                    "name": block.name,
                    "position": {"x": pos.x, "y": pos.y, "z": pos.z}
                })
    except Exception as e:
        print(f"Error al buscar bloques: {e}")
        
    return blocks

