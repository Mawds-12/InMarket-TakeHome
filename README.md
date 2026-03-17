precedent-brief/
├── README.md                   ← You are here
├── documentation/
│   ├── ARCHITECTURE.md         ← System design, data flow, layer responsibilities
│   ├── STARTUP_GUIDE.md        ← How to run the full stack locally
│   ├── API_CONTRACTS.md        ← All internal endpoint shapes (request + response)
│   └── ENV_REFERENCE.md        ← Every environment variable, what it does, where it goes
├── MCP/                        ← Wrapper microservice (FastAPI)
│   ├── README.md               ← MCP-specific setup and endpoint guide
│   ├── requirements.txt
│   └── ...
├── Backend/                    ← LLM agent + LangChain orchestration (FastAPI)
│   ├── README.md               ← Backend-specific setup and chain guide
│   ├── requirements.txt
│   └── ...
└── FrontEnd/                   ← Next.js single-page research workspace
    ├── README.md               ← Frontend-specific setup guide
    ├── package.json
    └── ...