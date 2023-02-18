{
  "mongodb_atlas": {
    "api_key": "your_mongodb_atlas_api_key",
    "group_id": "your_mongodb_atlas_group_id",
    "metrics": {
      "latency": {
        "thresholds": {
          "warning": 100,
          "critical": 500
        }
      },
      "cpu": {
        "thresholds": {
          "warning": 75,
          "critical": 90
        }
      },
      "memory": {
        "thresholds": {
          "warning": 75,
          "critical": 90
        }
      },
      "disk": {
        "thresholds": {
          "warning": 75,
          "critical": 90
        }
      },
      "connections": {
        "thresholds": {
          "warning": 1000,
          "critical": 5000
        }
      },
      "slow_queries": {
        "thresholds": {
          "warning": 5,
          "critical": 10
        }
      }
    }
  },
  "pagerduty": {
    "api_key": "your_pagerduty_api_key",
    "service_key": "your_pagerduty_service_key",
    "escalation_policy_id": "your_pagerduty_escalation_policy_id"
  }
}
