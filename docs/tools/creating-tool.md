# Tools

**Tools** are programs registered by developers in a public registry, enabling agents or applications to utilize them for performing specific tasks.
These tools can be implemented in Python or provided as pre-built binaries with limited functionality, and can be dynamically loaded by agents at runtime when required.

Agents can also leverage large language models (LLMs) to intelligently select the most appropriate tool based on the metadata of all available tools, enabling context-aware and optimized task execution.

## Onboarding a python tool:

This guide describes how to create, package, and structure a tool that can be executed using the `LocalToolExecutor` class. The executor expects tools to follow a specific file layout and implement a standard Python interface. This enables tools to be downloaded, initialized, and executed dynamically with configuration support.

---

### Step 1: Understand the Required Structure

Every tool must be provided in one of the following forms:

* A **directory** on the local filesystem.
* A **compressed archive** (`.zip` or `.tar.gz`) downloadable via a URL or path.

The internal structure must be:

```
tool_package/
└── code/
    ├── function.py            # Required: Implements the main execution class
    └── requirements.txt       # Optional: Python dependencies for the tool
```

> The top-level folder can be named anything, but it **must contain a `code/` subdirectory**.

---

### Step 2: Implement the Tool Interface

Inside `code/function.py`, define a class named `AgentSpaceV1Tool` with the following methods:

#### Required: `__init__`

```python
def __init__(self, tool_id: str, tool_data: dict):
```

* `tool_id`: Unique identifier of the tool.
* `tool_data`: Configuration parameters provided at runtime (e.g., thresholds, flags).

This method is used to initialize internal state or load models/configs.

#### Required: `execute`

```python
def execute(self, input_data: dict) -> dict:
```

* `input_data`: A dictionary of inputs, conforming to the `tools_api_spec.input`.
* Returns a dictionary matching the `tools_api_spec.output`.

This method is the main entry point for executing the tool's logic.

#### Optional: `execute_command`

```python
def execute_command(self, command_name: str, data: dict):
```

* `command_name`: A string identifying a specific operation.
* `data`: Input data relevant to that command.

This allows you to expose multiple operations or sub-features in your tool.

---

### Step 3: (Optional) Add Dependencies

If your tool depends on external Python packages, include a `requirements.txt` file:

#### Example: `code/requirements.txt`

```
numpy
pillow
requests
```

---

### Step 4: Create a Sample Tool

Here’s an example of a minimal tool that performs a simple greeting:

#### `code/function.py`

```python
class AgentSpaceV1Tool:
    def __init__(self, tool_id, tool_data):
        self.tool_id = tool_id
        self.config = tool_data

    def execute(self, input_data):
        name = input_data.get("name", "World")
        return {
            "message": f"Hello, {name} from tool {self.tool_id}"
        }

    def execute_command(self, command_name, data):
        if command_name == "uppercase":
            return data.get("text", "").upper()
        else:
            raise NotImplementedError(f"Unknown command: {command_name}")
```

---

### Step 5: Define Your Tool’s API Schema

Your tool must be described using a `tools_api_spec` when registering it. This helps systems understand what inputs it expects and what outputs it produces.

#### Example:

```json
{
  "input": {
    "name": {
      "type": "string",
      "description": "The name to greet"
    }
  },
  "output": {
    "message": {
      "type": "string",
      "description": "The resulting greeting"
    }
  }
}
```

This schema is stored in the database alongside the tool metadata and is used for validation, documentation, and UI generation.

---

### Step 6: Package and Register Your Tool

You can use either of these formats:

* Upload a directory structured as described.
* Compress the tool directory into a `.zip` or `.tar.gz` archive and host it (e.g., S3, GitHub, internal registry).

Register the tool in your system (e.g., MongoDB or API) using fields like:

```json
{
  "tool_id": "greeting-tool-v1",
  "tool_runtime_type": "python",
  "tool_source_code_link": "https://your-server.com/greeting-tool.zip",
  "tool_data": {
    "language": "en"
  },
  "tools_api_spec": {
    "input": { ... },
    "output": { ... }
  }
}
```

---

### Step 7: Execution Flow (Handled by LocalToolExecutor)

Once your tool is registered and a request is made to execute it, the following steps occur:

1. **Download or extract** the tool package.
2. **Install dependencies** from `requirements.txt` (if present).
3. **Import and initialize** the `AgentSpaceV1Tool` class with `tool_id` and `tool_data`.
4. **Run the `execute()` method** with the input payload.
5. Optionally, **run custom operations** via `execute_command()`.

---

### Summary

| Component                          | Required | Description                                                       |
| ---------------------------------- | -------- | ----------------------------------------------------------------- |
| `code/function.py`                 | Yes      | Contains `AgentSpaceV1Tool` with `__init__` and `execute` methods |
| `AgentSpaceV1Tool.execute`         | Yes      | Main entry point for tool execution                               |
| `AgentSpaceV1Tool.execute_command` | No       | Optional custom command-based execution                           |
| `code/requirements.txt`            | No       | Python dependencies for the tool                                  |
| `tools_api_spec`                   | Yes      | Input/output contract used for validation and API clients         |

---

## Sample python tool:

This guide describes how to build and register a tool. The example tool uses a weather API to predict the weather for the next day, based on the past N days of weather data.

---

### 1. Tool Directory Structure

Create a directory with the following layout:

```
weather-forecast-v1/
└── code/
    ├── function.py           # Required. Contains the tool's logic.
    └── requirements.txt      # Optional. Lists dependencies.
```

---

### 2. Tool Code (`code/function.py`)

This file must define a class `AgentSpaceV1Tool` with `__init__`, `execute`, and optionally `execute_command` methods.

```python
import requests

class AgentSpaceV1Tool:
    def __init__(self, tool_id, tool_data):
        self.tool_id = tool_id
        self.config = tool_data
        self.api_key = self.config.get("weather_api_key")
        self.api_base_url = self.config.get("weather_api_base_url")
        self.unit = self.config.get("temperature_unit", "metric")
        self.default_days = self.config.get("default_days", 7)

    def execute(self, input_data):
        location = input_data.get("location")
        past_days = input_data.get("past_days", self.default_days)

        if not location:
            raise ValueError("Missing required input: location")

        lat, lon = self._geocode_location(location)
        historical = self._fetch_past_weather(lat, lon, past_days)
        forecast = self._fetch_forecast(lat, lon)

        return {
            "predicted_temperature": forecast.get("temp"),
            "predicted_conditions": forecast.get("conditions")
        }

    def execute_command(self, command_name, data):
        if command_name == "geocode":
            location = data.get("location")
            return {"coordinates": self._geocode_location(location)}
        else:
            raise NotImplementedError(f"Unknown command: {command_name}")

    def _geocode_location(self, location):
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError("Invalid location or not found")
        return results[0]["lat"], results[0]["lon"]

    def _fetch_past_weather(self, lat, lon, days):
        return [{"day": i, "temp": 25 + i * 0.1} for i in range(days)]  # Simulated data

    def _fetch_forecast(self, lat, lon):
        url = f"{self.api_base_url}?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts&appid={self.api_key}&units={self.unit}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        next_day = data.get("daily", [])[1]
        return {
            "temp": next_day["temp"]["day"],
            "conditions": next_day["weather"][0]["description"]
        }
```

---

### 3. Requirements File (`code/requirements.txt`)

```text
requests
```

---

### 4. Create the Zip Archive

```bash
cd weather-forecast-v1
zip -r weather-forecast-v1.zip code/
```

---

### 5. Upload the Tool to the Assets Registry

You can host the zipped tool on any static file server. If you are using an **assets registry**, use the following `curl` command:

```bash
curl -X POST http://<server-url>/upload_asset \
     -H "Content-Type: multipart/form-data" \
     -F "asset=@./weather-forecast-v1.zip" \
     -F 'asset_metadata={
           "asset_name": "weather-forecast-v1",
           "asset_version": { "version": "1.0", "tag": "stable" },
           "asset_metadata": { "description": "Tool that predicts next day weather using OpenWeatherMap API" },
           "asset_tags": ["weather", "prediction", "api"]
         }'
```

For the documentation about assets registry, [refer to this link](https://docs.aigr.id/assets-db-registry/assets-db-registry/)


> On success, this returns a public URL like:
> `https://assets.example.com/tools/weather-forecast-v1.zip`

> Note: You can optionally use any public storage service of your own to store the tool.

---

### 6. Tool Registration JSON

Once uploaded, register the tool in your system using this JSON payload.

```json
{
  "tool_id": "weather-forecast-v1",
  "tool_metadata": {
    "author": "ClimateAI Team",
    "version": "1.0.0",
    "language": "python",
    "license": "MIT",
    "description": "Predicts the weather for the next day using past weather data and external API"
  },
  "tool_search_description": "Next-day weather forecasting tool using historical data and external API",
  "tool_tags": ["weather", "forecasting", "api", "time-series", "prediction"],
  "tool_type": "model-inference",
  "tool_sub_type": "weather-prediction",
  "tool_runtime_type": "python",
  "tools_api_spec": {
    "input": {
      "location": {
        "type": "string",
        "description": "City or region for which to forecast the weather"
      },
      "past_days": {
        "type": "integer",
        "description": "Number of past days to use for prediction",
        "min": 1,
        "max": 30
      }
    },
    "output": {
      "predicted_temperature": {
        "type": "number",
        "description": "Predicted temperature (in Celsius) for the next day"
      },
      "predicted_conditions": {
        "type": "string",
        "description": "Forecasted weather conditions (e.g., sunny, rainy)"
      }
    },
    "management": {
      "timeout": {
        "type": "number",
        "default": 60,
        "description": "Execution timeout in seconds"
      },
      "retries": {
        "type": "number",
        "default": 2,
        "description": "Number of times to retry API call on failure"
      }
    }
  },
  "tool_data": {
    "weather_api_key": "<YOUR_API_KEY>",
    "weather_api_base_url": "https://api.openweathermap.org/data/2.5/onecall",
    "temperature_unit": "metric",
    "default_days": 7
  },
  "tool_source_code_link": "https://assets.example.com/tools/weather-forecast-v1.zip",
  "tool_man_page_doc_link": "https://docs.example.com/tools/weather-forecast-v1"
}
```

---

### Final Notes

* Replace `<YOUR_API_KEY>` with your actual OpenWeatherMap API key.
* Replace the `tool_source_code_link` and `tool_man_page_doc_link` with actual URLs after upload.
* You can extend this tool to use a real historical weather API or integrate it with a local dataset.

---

## Creating a binary tool


### 1. Overview

`BinaryToolExecutor` allows execution of precompiled binaries by:

* Downloading or loading a zipped or directory-based tool package.
* Extracting or copying the binary file to a temporary location.
* Executing the binary with serialized JSON input and reading output from a file.

This pattern enables cross-language tool integration (C/C++, Go, Rust, etc.) in any container or host.

---

### 2. Tool Packaging Structure

Binary tools must be packaged into one of the following formats:

* A `.zip` or `.tar.gz` archive containing a single executable.
* A local folder containing the binary executable directly.

The expected structure is:

```
binary-tool-v1/
└── code/
    └── <binary_executable>   # The compiled binary file (no subdirectories)
```

**Important**: The top-level directory must contain a `code/` folder. The binary should be placed directly inside `code/`.

---

### 3. Tool Binary Interface Specification

The binary executable must adhere to the following contract:

* Accept **two command-line arguments**:

  1. A JSON string containing `tool_id`, `tool_data`, `mode`, and `input`.
  2. A path to the output file to write the JSON response.
* Write the output result to the output file in **valid JSON format**.

#### Input JSON example (received as CLI argument 1):

```json
{
  "tool_id": "binary-tool-v1",
  "tool_data": { "param": "value" },
  "mode": "input",
  "input": { "value": 42 }
}
```

#### Output JSON example (written to CLI argument 2):

```json
{
  "result": 43,
  "status": "success"
}
```

---

### 4. Example Tool (Go)

Here is a sample Go binary that increments a number:

#### `main.go`

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Input struct {
	ToolID   string                 `json:"tool_id"`
	ToolData map[string]interface{} `json:"tool_data"`
	Mode     string                 `json:"mode"`
	Input    map[string]interface{} `json:"input"`
}

func main() {
	if len(os.Args) < 3 {
		fmt.Println("Usage: <input_json> <output_file>")
		return
	}

	// Parse input
	var input Input
	err := json.Unmarshal([]byte(os.Args[1]), &input)
	if err != nil {
		fmt.Println("Invalid input JSON:", err)
		return
	}

	// Process
	val, ok := input.Input["value"].(float64)
	if !ok {
		fmt.Println("Missing or invalid 'value'")
		return
	}
	result := val + 1

	// Write output
	output := map[string]interface{}{
		"result": result,
		"status": "success",
	}
	outFile, err := os.Create(os.Args[2])
	if err != nil {
		fmt.Println("Error creating output file:", err)
		return
	}
	defer outFile.Close()

	json.NewEncoder(outFile).Encode(output)
}
```

#### Build and package:

```bash
go build -o binary_increment main.go
mkdir -p binary-tool-v1/code
mv binary_increment binary-tool-v1/code/
cd binary-tool-v1
zip -r binary-tool-v1.zip code/
```

---

### 5. Upload to Assets Registry (Optional)

You can upload the packaged binary to your asset registry:

```bash
curl -X POST http://<server-url>/upload_asset \
     -H "Content-Type: multipart/form-data" \
     -F "asset=@./binary-tool-v1.zip" \
     -F 'asset_metadata={
           "asset_name": "binary-increment-tool",
           "asset_version": { "version": "1.0", "tag": "stable" },
           "asset_metadata": { "description": "Increments a number by 1" },
           "asset_tags": ["binary", "example", "increment"]
         }'
```

You will receive a public URL like:
`https://assets.example.com/tools/binary-tool-v1.zip`

---

### 6. Tool Registration JSON

```json
{
  "tool_id": "binary-increment-tool",
  "tool_metadata": {
    "author": "CLI Tools Inc.",
    "version": "1.0.0",
    "language": "go",
    "license": "MIT",
    "description": "CLI tool that increments a number by 1"
  },
  "tool_search_description": "Command-line tool to increment a number",
  "tool_tags": ["binary", "math", "go"],
  "tool_type": "utility",
  "tool_sub_type": "increment",
  "tool_runtime_type": "binary",
  "tools_api_spec": {
    "input": {
      "value": {
        "type": "number",
        "description": "Value to be incremented"
      }
    },
    "output": {
      "result": {
        "type": "number",
        "description": "Incremented result"
      },
      "status": {
        "type": "string",
        "description": "Execution status"
      }
    },
    "management": {
      "timeout": {
        "type": "number",
        "default": 10,
        "description": "Max allowed time for execution"
      }
    }
  },
  "tool_data": {},
  "tool_source_code_link": "https://assets.example.com/tools/binary-tool-v1.zip",
  "tool_man_page_doc_link": "https://docs.example.com/tools/binary-increment-tool"
}
```

---

### Python Tool vs Binary Tool: Feature Comparison

| Feature                        | Python Tool (`LocalToolExecutor`)                                                   | Binary Tool (`BinaryToolExecutor`)                               |
| ------------------------------ | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Implementation Language**    | Python                                                                              | Any compiled language (e.g., Go, Rust, C++)                      |
| **Entry Class Required**       | `AgentSpaceV1Tool` with `__init__`, `execute`, and optionally `execute_command`     | No class required. Single executable with CLI-based input/output |
| **Input Interface**            | Method call with `input_data` as a Python dictionary                                | First CLI argument: serialized JSON string                       |
| **Output Interface**           | Method return value (Python dict)                                                   | Second CLI argument: path to write JSON output                   |
| **Dependencies**               | Python dependencies via `requirements.txt`                                          | All dependencies must be statically linked or bundled            |
| **Packaging Format**           | `.zip` or `.tar.gz` containing `code/function.py` and optionally `requirements.txt` | `.zip` or `.tar.gz` containing `code/<binary_file>`              |
| **Execution Environment**      | Python runtime with `pip`                                                           | System runtime that supports native binary execution             |
| **Dynamic Import Support**     | Yes (uses `importlib`)                                                              | No. Executes as a subprocess                                     |
| **Cross-platform Portability** | Platform-independent (requires Python)                                              | Platform-dependent (binaries must match host OS/arch)            |
| **Supports Custom Commands**   | Yes (`execute_command(command_name, data)`)                                         | No (returns static response for command interface)               |
| **Use Cases**                  | AI models, scripting tools, data transformations                                    | Low-latency utilities, compiled policies, fast CLI utilities     |
| **Execution Speed**            | Moderate (interpreted)                                                              | High (compiled)                                                  |
| **Flexibility**                | High (full Python support)                                                          | Low-to-moderate (restricted to command-line JSON I/O)            |
| **Deployment Overhead**        | Requires Python and dependency resolution                                           | Requires native compatibility and static linking                 |
| **Error Logging**              | Native exception handling and logging                                               | Must write errors to stdout/stderr or output file                |

---