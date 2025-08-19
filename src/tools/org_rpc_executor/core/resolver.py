import logging
from typing import Optional
from .db import ClusterLocalToolsDB
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("Resolver")
logging.basicConfig(level=logging.INFO)


class Resolver:
    def __init__(self, port: int = 50051):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config.")
        except Exception as e:
            logger.exception("Failed to load in-cluster K8s config.")
            raise

        self.core_v1 = client.CoreV1Api()
        self.db = ClusterLocalToolsDB()
        self.port = port
        self.cache = {}  

    def resolve(self, tool_name: str, node_id: str) -> Optional[str]:
        try:
            cache_key = (tool_name, node_id)

            if node_id in self.cache:
                logger.info(f"Cache hit for node_id '{node_id}'")
                ip = self.cache[node_id]
                return f"{ip}:{self.port}"

            tool = self.db.get_by_name_and_node(tool_name, node_id)
            if not tool:
                logger.warning(
                    f"Tool '{tool_name}' not found on node '{node_id}'")
                return None

            nodes = self.core_v1.list_node()
            for node in nodes.items:
                labels = node.metadata.labels or {}
                if labels.get("nodeID") == node_id:
                    for addr in node.status.addresses:
                        if addr.type == "InternalIP":
                            ip = addr.address
                            self.cache[node_id] = ip
                            logger.info(
                                f"Resolved IP for node_id '{node_id}': {ip}")
                            return f"{ip}:{self.port}"

            logger.warning(
                f"No matching node found in Kubernetes for node_id '{node_id}'")
            return None

        except ApiException as e:
            logger.exception("Kubernetes API error during node resolution")
            raise
        except Exception as e:
            logger.exception("Unexpected error during tool resolution")
            raise
