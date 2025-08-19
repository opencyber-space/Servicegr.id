curl -X POST http://localhost:10000/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "dummy",
           "version": "1.0",
           "release_tag": "stable",
           "metadata": {"author": "admin", "category": "analytics"},
           "tags": "analytics,ai",
           "code": "/home/cognitifai/Documents/aiosv1/services/search_server/samples/policy/policy.tar.xz",
           "code_type": "tar.xz",
           "type": "policy",
           "policy_input_schema": {"type": "object", "properties": {"input": {"type": "string"}}},
           "policy_output_schema": {"type": "object", "properties": {"output": {"type": "string"}}},
           "policy_settings_schema": {},
           "policy_parameters_schema": {},
           "policy_settings": {},
           "policy_parameters": {},
           "description": "A policy for factual analysis.",
           "functionality_data": {"strategy": "ML-based"}
         }'
