import asyncio
from typing import List, Dict, Callable, Any
from src.core.logger import logger

class ToolService:
    """
    Registry for tools (functions) that the AI can call.
    """
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, parameters: Dict, callback: Callable):
        """Registers a new tool that the LLM can use."""
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }
        self._callbacks[name] = callback
        logger.info(f"Tool registered: {name}")

    def get_tools_schema(self) -> List[Dict]:
        """Returns the tools in the format required by LLM providers (OpenAI/Mistral)."""
        return list(self._tools.values())

    async def execute_tool(self, name: str, arguments: Dict) -> str:
        """Executes a tool and returns the result as string."""
        if name not in self._callbacks:
            return f"Error: Tool {name} not found."
        
        try:
            logger.info(f"Executing tool: {name}", args=arguments)
            # Handle both sync and async callbacks
            callback = self._callbacks[name]
            if asyncio.iscoroutinefunction(callback):
                result = await callback(**arguments)
            else:
                result = callback(**arguments)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing tool {name}", error=str(e))
            return f"Error executing {name}: {str(e)}"

# --- Ejemplo de Herramienta para Llamadas/Chat ---
async def get_delivery_status(order_id: str):
    # Simular latencia de red/DB
    await asyncio.sleep(0.1)
    return f"El pedido {order_id} se encuentra en camino y llegará hoy antes de las 6 PM."

# Instancia global (o inyectada)
tool_manager = ToolService()
tool_manager.register_tool(
    name="consultar_envio",
    description="Obtiene el estado actual de un pedido usando su ID",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "El ID del pedido del cliente"}
        },
        "required": ["order_id"]
    },
    callback=get_delivery_status
)
