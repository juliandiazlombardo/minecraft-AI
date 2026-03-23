"""
tool_registry.py: Registra y expone las funciones de Python a la IA.
"""
from tools.movement import mover_a_coordenada
from tools.combat import atacar_entidad
from tools.inventory import equipar_item

class ToolRegistry:
    def __init__(self, bot):
        self.bot = bot # Necesitamos la referencia al bot para ejecutar las acciones

    def get_available_tools_schema(self):
        """
        Devuelve el formato JSON-schema de las herramientas para que la IA sepa qué puede hacer.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "mover_a_coordenada",
                    "description": "Camina hacia una coordenada X, Z específica en el mundo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "Coordenada X"},
                            "z": {"type": "integer", "description": "Coordenada Z"}
                        },
                        "required": ["x", "z"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mirar_alrededor",
                    "description": "El bot mira a su alrededor, útil para forzar una actualización visual.",
                    "parameters": {
                        "type": "object",
                        "properties": {} # Sin parámetros
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, args: dict):
        """
        Ejecuta la función de Python correspondiente.
        """
        print(f"⚡ Ejecutando tool: {tool_name}({args})")
        
        try:
            if tool_name == "mover_a_coordenada":
                # Implementación muy básica, para moverse bien se usa 'mineflayer-pathfinder'
                # Por ahora solo es un esqueleto de prueba.
                print(f"[{tool_name}] Bot simulando movimiento a X:{args.get('x')} Z:{args.get('z')}")
                return "Hecho."
            
            elif tool_name == "mirar_alrededor":
                print(f"[{tool_name}] Bot mirando...")
                return "Miraste a tu alrededor."
                
            else:
                return f"Herramienta desconocida: {tool_name}"
        except Exception as e:
            return f"Error ejecutando la herramienta: {e}"
