import yaml
import os
from src.domain.interfaces import IPromptRepository
from src.core.logger import logger

class YamlPromptRepository(IPromptRepository):
    def __init__(self, file_path: str = "config/prompts.yaml"):
        self.file_path = file_path
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        if not os.path.exists(self.file_path):
            logger.warning("Prompts YAML file not found, using defaults", path=self.file_path)
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f) or {}
                logger.info("Prompts loaded successfully", companies=list(self.prompts.keys()))
        except Exception as e:
            logger.error("Failed to load prompts YAML", error=str(e))

    def get_prompt_for_company(self, company_id: str, default_prompt: str) -> str:
        company_config = self.prompts.get(company_id, {})
        return company_config.get("system_prompt", default_prompt)
