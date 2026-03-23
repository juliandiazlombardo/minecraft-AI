"""
brain.py: Controla la interacción con los LLMs y la toma de decisiones.
"""
import os
import json
from openai import OpenAI
import google.generativeai as genai

class AIBrain:
    def __init__(self, provider="openai"):
        self.provider = provider.lower()
        self.provider = provider.lower()
        self.tools = []
        self.skills = []
        self.goal = ""
        self.plan = ""
        self.identity = "Eres un agente de IA jugando Minecraft."
        self.system_prompt = ""
        self.chat_history = []
        
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no encontrada en .env")
            self.client = OpenAI(api_key=api_key)
            
        elif self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no encontrada en .env")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
        # Para agregar Anthropic o HuggingFace, se implementaría aquí de forma similar
    def set_tools(self, tools:list):
        self.tools += tools

    def set_skills(self, skills:str):
        self.skills = skills

    def set_goal(self, goal:str):
        self.goal = goal

    def set_plan(self, plan:str):
        self.plan = plan

    def set_identity(self, identity:str):
        self.identity = identity
        
    def update_system_prompt(self):
        self.system_prompt = f""" {self.identity} 
        Tienes acceso a Tools (funciones) y Skills (conocimiento) 
        tools: 
        {self.tools} 
        skills: 
        {self.skills} 
        Ayudate de ellos para cumplir tu meta 
        meta: 
        {self.goal} 
        para lograr tu meta debes seguir el siguiente plan: 
        {self.plan}
        """
        
    def add_to_history(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})
        # Mantener historial corto para no gastar tokens
        if len(self.chat_history) > 20: 
            self.chat_history = self.chat_history[-20:]

    def decide_action(self, observation: str, available_tools: list) -> dict:
        """
        Envía la observación actual al LLM junto con las herramientas disponibles,
        y retorna la decisión de la IA (qué tool usar y con qué argumentos).
        """
        self.add_to_history("user", f"Observación del mundo:\n{observation}\n¿Qué haces ahora?")
        
        if self.provider == "openai":
            return self._call_openai(available_tools)
        elif self.provider == "gemini":
            return self._call_gemini(available_tools)
        else:
            return {"error": f"Proveedor {self.provider} no implementado completamente."}

    def _call_openai(self, tools: list):
        messages = [{"role": "system", "content": self.system_prompt}] + self.chat_history
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools if len(tools) > 0 else None,
                tool_choice="auto" if len(tools) > 0 else "none"
            )
            
            message = response.choices[0].message
            
            # Si el modelo decidió llamar a una herramienta
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                self.add_to_history("assistant", f"Invocando tool: {function_name} con {arguments}")
                
                return {
                    "action": "call_tool",
                    "tool": function_name,
                    "args": arguments
                }
            else:
                self.add_to_history("assistant", message.content)
                return {
                    "action": "chat",
                    "message": message.content
                }
                
        except Exception as e:
            print(f"Error en OpenAI API: {e}")
            return {"action": "error", "message": str(e)}

    def _call_gemini(self, tools: list):
        # Implementación simplificada para Gemini (las tools en Gemini usan un formato distinto, 
        # esto es solo una simulación temporal)
        try:
            prompt = self.system_prompt + "\n\n"
            for msg in self.chat_history:
                prompt += f"{msg['role']}: {msg['content']}\n"
                
            response = self.model.generate_content(prompt)
            self.add_to_history("assistant", response.text)
            return {
                "action": "chat",
                "message": response.text
            }
        except Exception as e:
            return {"action": "error", "message": str(e)}

