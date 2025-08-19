curl -X POST http://localhost:10000/executor \
     -H "Content-Type: application/json" \
     -d '{
           "executor_id": "executor-0",
           "executor_host_uri": "http://localhost:10250",
           "executor_metadata": {"os": "Linux", "version": "1.0"},
           "executor_hardware_info": {"cpu": "Intel Xeon", "ram": "16GB"},
           "executor_status": "healthy"
         }'
