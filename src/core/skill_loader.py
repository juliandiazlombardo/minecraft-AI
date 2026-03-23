"""
skill_loader.py: Lee y parsea los archivos Markdown de la carpeta 'skills'.
"""
import os

class SkillLoader:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = skills_dir
        self.skills = {}

    def load_all_skills(self):
        """
        Lee todos los archivos .md en la carpeta de skills y los guarda en memoria.
        """
        if not os.path.exists(self.skills_dir):
            print(f"La carpeta '{self.skills_dir}' no existe.")
            return

        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(self.skills_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    skill_name = filename.replace(".md", "")
                    self.skills[skill_name] = content
                    
        print(f"Se cargaron {len(self.skills)} skills.")

    def get_skill(self, skill_name: str) -> str:
        """
        Retorna el contenido de un skill específico.
        """
        return self.skills.get(skill_name, f"Skill '{skill_name}' no encontrado.")
        
    def get_all_skills_descriptions(self) -> str:
        """
        Retorna un resumen de todos los skills disponibles para inyectar en el prompt base.
        """
        if not self.skills:
            return "No hay skills disponibles."
            
        summary = "Skills disponibles:\n"
        for idx, skill in enumerate(self.skills.keys()):
            summary += f"{idx + 1}. {skill}\n"
        return summary

