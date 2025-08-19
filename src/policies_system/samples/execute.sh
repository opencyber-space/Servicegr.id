curl -X POST http://localhost:10000/executor/executor-0/execute_policy \
     -H "Content-Type: application/json" \
     -d '{
           "policy_rule_uri": "fact-teller:1.0-stable",
           "input_data": {"a": 10, "b": 30},
           "parameters": {}
         }'
