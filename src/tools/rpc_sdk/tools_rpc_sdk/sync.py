import os
import requests
import logging
from .tool_registry import global_tool_registry

logger = logging.getLogger("ToolRegistrySync")
logging.basicConfig(level=logging.INFO)


class ToolRegistrySyncer:
    def __init__(self):
        self.registry_url = os.getenv("ORG_SYSTEM_TOOLS_REGISTRY_URL")
        if not self.registry_url:
            logger.warning("ORG_SYSTEM_TOOLS_REGISTRY_URL not set. Tool sync skipped.")
            self.enabled = False
        else:
            logger.info(f"Tool registration enabled: {self.registry_url}")
            self.enabled = True

    def sync_tools(self):
        if not self.enabled:
            return

        for tool in global_tool_registry.list_tools().values():
            try:
                delete_url = f"{self.registry_url}/tools/{tool.name}/{tool.metadata.get('node_id', '')}"
                create_url = f"{self.registry_url}/tools"

                # Delete first (idempotent cleanup)
                try:
                    resp = requests.delete(delete_url, timeout=5)
                    logger.info(f"Deleted tool: {tool.name}, status: {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Delete failed for {tool.name}: {e}")

                # Insert
                payload = {
                    "name": tool.name,
                    "node_id": tool.metadata.get("node_id", ""),
                    "input_spec": tool.input_spec,
                    "metadata": tool.metadata,
                    "description": tool.description
                }
                resp = requests.post(create_url, json=payload, timeout=5)
                if resp.status_code in [200, 201]:
                    logger.info(f"Registered tool: {tool.name}")
                else:
                    logger.error(f"Failed to register tool: {tool.name}. Response: {resp.text}")
            except Exception as e:
                logger.exception(f"Failed to sync tool: {tool.name}")
