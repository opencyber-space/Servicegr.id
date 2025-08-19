## Functions

**Functions** are remote code components registered by developers in a public registry, allowing agents or applications to invoke them to perform specific tasks.
These functions can be hosted on any server and exposed via REST or WebSocket interfaces, enabling seamless integration across distributed environments.

Agents can also leverage large language models (LLMs) to intelligently select the most appropriate function based on the metadata of all available functions, ensuring context-aware and efficient execution.

--- 

## Function Development SDK 

This SDK provides a structured interface for writing, validating, and deploying functions that can be exposed via REST or WebSocket protocols. It ensures standardization across function execution and supports runtime validation against the API spec defined in the function registry.

---

## 📦 agent\_functions SDK Installation Guide

The `agent_functions` SDK is a Python library that provides tools to develop, validate, and serve modular functions via REST or WebSocket. It is commonly used in function-based AI systems and agent orchestration.

---

### Directory Structure

Ensure you're inside the correct repository and path:

```bash
cd systems/functions/functions_server_lib
```

This is the directory containing the `setup.py` or `pyproject.toml` for the `agent_functions` SDK.

---

### Installation

Use pip to install the package in **editable mode**, which links the local code directly into your Python environment:

```bash
pip3 install -e .
```

This will install the SDK under the package name:

```
agent_functions
```

---

### Verifying Installation

After installation, you can verify it in Python:

```python
import agent_functions
print(agent_functions.__file__)
```

---

### Usage Example

```python
from agent_functions.server import start_server

class MyFunction:
    def eval(self, data: dict):
        return {"echo": data}

if __name__ == "__main__":
    start_server(MyFunction(), mode="rest", port=8080)
```
---

---

### 1. Structure of a Function

To write a function using the SDK, the function class must:

* Implement an `eval(self, data: dict)` method
* Be passed into the SDK via `create_handler()`
* Support structured input as per the `function_api_spec.input` field from the registry

#### Basic Function Structure

```python
class MyFunction:
    def __init__(self):
        # Optional: initialization logic
        pass

    def eval(self, data: dict) -> dict:
        # Main function logic
        return { "result": "OK" }
```

---

### 2. Writing a Function

You are expected to define a function class with an `eval()` method that receives input as a Python dictionary and returns a dictionary-compatible output.

#### Example

```python
class AddFunction:
    def __init__(self):
        pass

    def eval(self, data: dict) -> dict:
        a = data.get("a")
        b = data.get("b")
        return { "sum": a + b }
```

You can optionally include validation metadata in the registry for this function (e.g., `a` and `b` must be numbers).

---

### 3. SDK Functions and Capabilities

#### `Handler` Class

The `Handler` wraps a function instance and provides:

| Method                        | Description                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| `__init__(function_instance)` | Initializes with a user-defined function object implementing `eval()`                   |
| `set_validation_data(dict)`   | Accepts input validation schema in dictionary form (usually from registry `input` spec) |
| `validate(data)`              | Validates input data against the schema using rules like type, min, max, pattern, etc.  |
| `execute(data)`               | Executes the function via `eval()` with the validated data                              |

#### `create_handler(obj)`

Creates and returns a `Handler` instance from a function object.

#### Validation Support

Supports type validation for:

* `string` (with optional `choices`)
* `number` (with `min`, `max`)
* `array`
* `object` (recursive validation via `properties`)
* `any` (bypasses validation)

---

### 4. Integrating with the SDK

Use `start_server()` to launch your function over a REST or WebSocket server. You only need to implement the function class and pass it to the SDK.

#### Syntax

```python
start_server(function_instance, mode="rest", port=5555)
```

| Parameter           | Description                                 |
| ------------------- | ------------------------------------------- |
| `function_instance` | An instance of a class with `eval()` method |
| `mode`              | `"rest"` or `"websocket"`                   |
| `port`              | Port number to expose the server            |

The `start_server()` method internally:

1. Wraps your function with a `Handler`
2. Launches a REST or WebSocket server
3. Listens on the given port

---

### 5. End-to-End Example

#### File: `my_function.py`

```python
class MultiplyFunction:
    def __init__(self):
        pass

    def eval(self, data: dict) -> dict:
        x = data.get("x")
        y = data.get("y")
        return { "product": x * y }
```

#### File: `main.py`

```python
from sdk import start_server
from my_function import MultiplyFunction

if __name__ == "__main__":
    func = MultiplyFunction()
    start_server(func, mode="rest", port=8080)
```

#### Sample Input (POST `/` on port 8080)

```json
{
  "x": 5,
  "y": 4
}
```

#### Sample Output

```json
{
  "product": 20
}
```

---

### Notes

* To enable validation, call `handler.set_validation_data(spec_dict)` before invoking `.execute()`.
* The input spec format should align with the `function_api_spec.input` structure used in the registry.
* The server implementations (`FunctionServer`, `FunctionWebSocketServer`) are expected to parse incoming requests, pass the payload to the handler, and return output.

Here’s a **real-world end-to-end example** of a function using the SDK to wrap a **Weather Data API client**, exposing it via REST using the `Handler`-based function SDK.

---

## 🌦️ Real-World Example: Weather Data Fetcher

This function uses the [OpenWeatherMap API](https://openweathermap.org/current) to fetch current weather data for a given city.

---

### 1. Weather Function Implementation

#### File: `weather_function.py`

```python
import requests

class WeatherFunction:
    def __init__(self):
        self.api_key = "<YOUR_OPENWEATHERMAP_API_KEY>"
        self.api_url = "http://api.openweathermap.org/data/2.5/weather"

    def eval(self, data: dict) -> dict:
        city = data.get("city")
        if not city:
            raise ValueError("Missing 'city' in input")

        response = requests.get(self.api_url, params={
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        })

        if response.status_code != 200:
            raise Exception(f"API error: {response.text}")

        weather = response.json()
        return {
            "city": city,
            "temperature": weather["main"]["temp"],
            "description": weather["weather"][0]["description"]
        }
```

---

### 2. Start the Server with SDK

#### File: `main.py`

```python
from sdk import start_server
from weather_function import WeatherFunction

if __name__ == "__main__":
    start_server(WeatherFunction(), mode="rest", port=8000)
```

---

### 3. (Optional) Add Validation

If using `Handler` directly and not just `start_server`, you could inject the input validation like this:

```python
handler = create_handler(WeatherFunction())
handler.set_validation_data({
    "city": {
        "type": "string",
        "description": "City name to fetch weather for"
    }
})
```

---

### 4. API Call Example

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"city": "Bangalore"}'
```

---

### 5. Expected Output

```json
{
  "city": "Bangalore",
  "temperature": 26.3,
  "description": "light rain"
}
```

---

### 6. Registry Metadata Example (`function_api_spec`)

This is what the registry entry for this function might look like:

```json
{
  "input": {
    "city": {
      "type": "string",
      "description": "City name to fetch weather for"
    }
  },
  "output": {
    "city": { "type": "string" },
    "temperature": { "type": "number" },
    "description": { "type": "string" }
  },
  "management": {
    "timeout": { "type": "number", "default": 10 }
  }
}
```

---

## Packaging the function using the container image

To containerize your function using the `agent_functions` SDK, you can build on top of the official base image:

```
FROM agentspacev1/functions_lib_base:v1
```

This base image includes:

* Pre-installed `agent_functions` SDK
* Python runtime environment
* Dependencies required for REST and WebSocket servers

---

### Example `Dockerfile`

```dockerfile
FROM agentspacev1/functions_lib_base:v1

# Set working directory
WORKDIR /app

# Copy your function files
COPY . /app

# Set default command to start your function
CMD ["python3", "main.py"]
```

---

### Example Project Structure

```
my-function/
├── main.py                # Starts the server using start_server()
├── my_function.py         # Your custom function logic
├── Dockerfile
```

---

### Build the Docker Image

```bash
docker build -t my-function-image .
```

---

### Run the Container

```bash
docker run -p 8080:8080 my-function-image
```

The function will now be accessible via:

```
http://localhost:8080
```

---

## Registering the function:

Once you have written and containerized your function, you must register it with the **Functions Registry** so it can be discovered, validated, and invoked by other agents or services.

The registration is done via a REST API call to the `/create` endpoint of the Functions Registry server.

---

### API Endpoint

**POST** `/create`

Registers a new function with the registry. The function must comply with the registry schema.

---

### Sample Registration Payload

```json
{
  "function_name": "weather_lookup",
  "function_version": {
    "version": "v1.0.0",
    "tag": "stable"
  },
  "function_type": "data-processing",
  "function_sub_type": "weather",
  "function_description": "Fetches real-time weather data for a given city using OpenWeatherMap API.",
  "function_tags": ["weather", "api", "external"],
  "function_protocol_type": "http",
  "function_url": "http://localhost:8000",
  "function_api_spec": {
    "input": {
      "city": {
        "type": "string",
        "description": "Name of the city to fetch weather for"
      }
    },
    "output": {
      "city": { "type": "string" },
      "temperature": { "type": "number" },
      "description": { "type": "string" }
    },
    "management": {
      "timeout": { "type": "number", "default": 10 }
    }
  },
  "function_calling_data": {
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "function_man_page": "https://docs.example.com/functions/weather_lookup"
}
```

---

### Example `curl` Command

```bash
curl -X POST http://localhost:3000/create \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "weather_lookup",
    "function_version": {
      "version": "v1.0.0",
      "tag": "stable"
    },
    "function_type": "data-processing",
    "function_sub_type": "weather",
    "function_description": "Fetches real-time weather data for a given city using OpenWeatherMap API.",
    "function_tags": ["weather", "api", "external"],
    "function_protocol_type": "http",
    "function_url": "http://localhost:8000",
    "function_api_spec": {
      "input": {
        "city": {
          "type": "string",
          "description": "Name of the city to fetch weather for"
        }
      },
      "output": {
        "city": { "type": "string" },
        "temperature": { "type": "number" },
        "description": { "type": "string" }
      },
      "management": {
        "timeout": { "type": "number", "default": 10 }
      }
    },
    "function_calling_data": {
      "headers": {
        "Content-Type": "application/json"
      }
    },
    "function_man_page": "https://docs.example.com/functions/weather_lookup"
  }'
```

---

### After Registration

Once registered:

* The function is stored in the registry with a unique `function_id` (auto-generated as `function_name:version-tag`)
* It can be discovered via query or search APIs
* It can be invoked by orchestration agents or external SDKs

---


