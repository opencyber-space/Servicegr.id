curl -X POST http://localhost:10000/function/deployments/create/executor-0 \
     -H "Content-Type: application/json" \
     -d '{
           "name": "fact-teller-deployment",
           "policy_rule_uri": "fact-teller:1.0-stable",
           "policy_rule_parameters": {},
           "replicas": 2,
           "autoscaling": false,
           "function_metadata": {"description": "Fact Teller Deployment"},
           "function_tags": ["analytics", "AI"]
         }'