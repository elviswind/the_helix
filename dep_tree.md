start_services.sh (ROOT)
├── config.py
├── run_worker.py
│   └── celery_app.py
│       ├── orchestrator_agent.py
│       ├── research_agent.py
│       └── synthesis_agent.py
├── main.py
│   ├── models.py
│   ├── services.py
│   ├── orchestrator_agent.py
│   └── synthesis_agent.py
├── start_mcp_server.py
│   └── mcp_api.py
│       ├── models.py
│       ├── pydantic_models.py
│       ├── orchestrator.py
│       │   ├── models.py
│       │   ├── pydantic_models.py
│       │   ├── celery_app.py
│       │   ├── research_agent.py
│       │   └── synthesis_agent.py
│       ├── tools.py
│       │   ├── sec_parser.py
│       │   └── orchestrator_agent.py
│       └── synthesis_agent.py
└── models.py