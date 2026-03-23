import os
import time
from dotenv import load_dotenv

from core.bot_client import MinecraftBot
from core.brain import AIBrain
from core.perception import get_bot_status, get_nearby_blocks
from core.skill_loader import SkillLoader
from core.tool_registry import ToolRegistry

def main():
    load_dotenv()
    print("Iniciando sistema de Minecraft AI Agent...")
    
    # 1. Iniciar conexión
    bot_client = MinecraftBot()
    bot = bot_client.bot
    
    # 2. Cargar Skills (Conocimiento en Markdown)
    skill_loader = SkillLoader()
    skill_loader.load_all_skills()
    
    # 3. Inicializar Brain (LLM)
    brain = AIBrain(provider="openai")
    
    # Inyectar las skills disponibles al prompt del sistema
    base_prompt = brain.system_prompt
    skills_context = skill_loader.get_all_skills_descriptions()
    brain.set_skills(skills_context)
    
    brain.update_system_prompt() # <=== fix: update_system_prompt se implementa diferente ahora
    
    # 4. Registrar Tools (Acciones en Python)
    tool_registry = ToolRegistry(bot)
    
    # Un pequeño loop para asegurarnos que el bot haya espawneado antes de pensar
    time.sleep(3)
    
    print("\n--- INICIANDO BUCLE DE AGENTE ---")
    try:
        while True:
            # A) PERCIBIR EL MUNDO
            status = get_bot_status(bot)
            blocks = get_nearby_blocks(bot, radius=5)
            
            observacion = f"Estado actual: Vida {status.get('health')}, Comida {status.get('food')}\n"
            observacion += f"Posición: {status.get('position')}\n"
            observacion += f"Bloques cercanos (no aire): {[b['name'] for b in blocks[:5]]}..."
            
            # B) PENSAR (Decidir qué hacer)
            tools_schema = tool_registry.get_available_tools_schema()
            
            print("\n[Agente Pensando...]")
            decision = brain.decide_action(observacion, tools_schema)
            
            # C) ACTUAR
            if decision.get("action") == "call_tool":
                tool_name = decision["tool"]
                args = decision["args"]
                # Ejecutar
                resultado = tool_registry.execute_tool(tool_name, args)
                # Informar al cerebro del resultado
                brain.add_to_history("user", f"Resultado de tool '{tool_name}': {resultado}")
                
            elif decision.get("action") == "chat":
                print(f"[Agente Dice] {decision['message']}")
                
            elif decision.get("action") == "error":
                print(f"[Error del Cerebro] {decision['message']}")

            # Pausa para no spamear la API muy rápido (buena práctica)
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nCerrando agente y desconectando bot...")

if __name__ == "__main__":
    main()


