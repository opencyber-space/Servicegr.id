from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from pymongo import MongoClient, errors
from pymongo.collection import Collection

logger = logging.getLogger("ClusterLocalToolsDB")
logging.basicConfig(level=logging.INFO)


@dataclass
class ClusterLocalTools:
    name: str
    func: Callable[[bytes], bytes]
    node_id: str
    input_spec: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "input_spec": self.input_spec,
            "metadata": self.metadata,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], func: Callable[[bytes], bytes]):
        return cls(
            name=data.get("name", ""),
            func=func,
            node_id=data.get("node_id", ""),
            input_spec=data.get("input_spec", {}),
            metadata=data.get("metadata", {}),
            description=data.get("description", "")
        )


class ClusterLocalToolsDB:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "tools_db"):
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.collection: Collection = self.db["cluster_local_tools"]
            logger.info("Connected to MongoDB for ClusterLocalToolsDB.")
        except errors.PyMongoError as e:
            logger.exception("Failed to connect to MongoDB.")
            raise

    def create(self, tool: ClusterLocalTools) -> str:
        try:
            tool_dict = tool.to_dict()
            result = self.collection.insert_one(tool_dict)
            logger.info(
                f"Inserted tool '{tool.name}' for node '{tool.node_id}'")
            return str(result.inserted_id)
        except Exception as e:
            logger.exception(
                f"Failed to create tool '{tool.name}' for node '{tool.node_id}'")
            raise

    def get_by_name_and_node(self, name: str, node_id: str) -> Optional[ClusterLocalTools]:
        try:
            data = self.collection.find_one({"name": name, "node_id": node_id})
            if data:
                logger.info(f"Retrieved tool '{name}' for node '{node_id}'")
                # Placeholder
                return ClusterLocalTools.from_dict(data, func=lambda x: b"")
            return None
        except Exception as e:
            logger.exception(
                f"Failed to get tool '{name}' for node '{node_id}'")
            raise

    def get_all_by_node(self, node_id: str) -> List[ClusterLocalTools]:
        try:
            tools = []
            for doc in self.collection.find({"node_id": node_id}):
                tools.append(ClusterLocalTools.from_dict(
                    doc, func=lambda x: b""))  # Placeholder
            logger.info(f"Fetched {len(tools)} tools for node '{node_id}'")
            return tools
        except Exception as e:
            logger.exception(f"Failed to fetch tools for node '{node_id}'")
            raise

    def update(self, name: str, node_id: str, updated_fields: Dict[str, Any]) -> bool:
        try:
            result = self.collection.update_one(
                {"name": name, "node_id": node_id},
                {"$set": updated_fields}
            )
            if result.modified_count > 0:
                logger.info(f"Updated tool '{name}' for node '{node_id}'")
                return True
            logger.warning(
                f"No updates made to tool '{name}' for node '{node_id}'")
            return False
        except Exception as e:
            logger.exception(
                f"Failed to update tool '{name}' for node '{node_id}'")
            raise

    def delete(self, name: str, node_id: str) -> bool:
        try:
            result = self.collection.delete_one(
                {"name": name, "node_id": node_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted tool '{name}' from node '{node_id}'")
                return True
            logger.warning(
                f"No tool '{name}' found to delete on node '{node_id}'")
            return False
        except Exception as e:
            logger.exception(
                f"Failed to delete tool '{name}' from node '{node_id}'")
            raise
