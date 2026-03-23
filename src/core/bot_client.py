"""
bot_client.py: Maneja la conexión pura a Minecraft usando la librería 'javascript' y 'mineflayer'.
"""
import os
import time
from javascript import require, On, Once, AsyncTask

class MinecraftBot:
    def __init__(self):
        # Al poner 'require', la librería de Python descargará node.js y la librería de npm
        # automáticamente en un caché local si no la tienes.
        self.mineflayer = require('mineflayer')
        
        host = os.getenv('MINECRAFT_SERVER_HOST', 'localhost')
        port = int(os.getenv('MINECRAFT_SERVER_PORT', 25565))
        username = os.getenv('BOT_USERNAME', 'Agent001')

        print(f"Conectando a {host}:{port} como '{username}'...")
        
        self.bot = self.mineflayer.createBot({
            'host': host,
            'port': port,
            'username': username
        })

        self.setup_event_listeners()

    def setup_event_listeners(self):
        """Configura los eventos de Mineflayer manejados en Python."""
        
        @On(self.bot, 'spawn')
        def handle_spawn(this, *args):
            print("¡El bot ha spawneado en el mundo exitosamente!")

        @On(self.bot, 'chat')
        def handle_chat(this, username, message, *args):
            if username == self.bot.username:
                return
            print(f"[Chat] {username}: {message}")

        @On(self.bot, 'error')
        def handle_error(this, err, *args):
            print(f"[Error del Bot] {err}")
            
        @On(self.bot, 'kicked')
        def handle_kicked(this, reason, loggedIn, *args):
            print(f"[Bot Expulsado] Razón: {reason}")

    def walk(self, direction: str, n_of_ticks: int):
        """
        Activa el estado de control de movimiento para la dirección dada
        durante un número específico de ticks (1 tick = 50ms).
        """
        # Mineflayer soporta controles como 'forward', 'back', 'left', 'right', 'jump', etc.
        self.bot.setControlState(direction, True)
        
        # 1 tick de Minecraft equivale a 0.05 segundos (50 milisegundos)
        time.sleep(n_of_ticks * 0.05)
        
        # Detenemos el movimiento
        self.bot.setControlState(direction, False)
