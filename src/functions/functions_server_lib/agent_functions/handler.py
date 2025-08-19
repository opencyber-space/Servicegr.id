
class Handler:

    def __init__(self, function_instance) -> None:
        self.validator_data = {}
        self.function_instance = function_instance

    def set_validation_data(self, validator_dict={}):
        self.validator = validator_dict

    def validate(self, data):

        if not self.validator_data:
            return

        try:
            spec = self.validator_data
            path = "root"
            if not isinstance(spec, dict):
                raise ValueError(
                    f"Invalid API spec at {path}. Must be a dict.")

            for key, constraints in spec.items():
                if key not in data:
                    raise ValueError(
                        f"Missing required field '{key}' at {path}.")

                value = data[key]
                field_type = constraints.get("type", "any")

                # Type validation logic
                if field_type == "number":
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"Field '{key}' at {path} must be a number.")
                    if "min" in constraints and value < constraints["min"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be >= {constraints['min']}.")
                    if "max" in constraints and value > constraints["max"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be <= {constraints['max']}.")
                elif field_type == "string":
                    if not isinstance(value, str):
                        raise ValueError(
                            f"Field '{key}' at {path} must be a string.")
                    if "choices" in constraints and value not in constraints["choices"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be one of {constraints['choices']}.")
                elif field_type == "array":
                    if not isinstance(value, list):
                        raise ValueError(
                            f"Field '{key}' at {path} must be an array.")
                elif field_type == "object":
                    if not isinstance(value, dict):
                        raise ValueError(
                            f"Field '{key}' at {path} must be an object.")
                    nested_spec = constraints.get("properties", {})
                    self.validate(value, nested_spec, path=f"{path}.{key}")
                elif field_type == "any":
                    pass  # No validation required for "any"
                else:
                    raise ValueError(
                        f"Unsupported type '{field_type}' for field '{key}' at {path}.")
        except Exception as e:
            raise e

    def execute(self, data: dict):
        try:

            return self.function_instance.eval(
                data
            )

        except Exception as e:
            raise e


def create_handler(obj):
    try:
        return Handler(obj)
    except Exception as e:
        raise e
