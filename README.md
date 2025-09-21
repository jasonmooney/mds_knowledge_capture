# MDS Knowledge Capture Agent

An agentic AI agent for autonomously capturing and managing Cisco MDS documentation PDFs with RAG integration, built using LangChain/LangGraph/LangSmith.

## Overview

This agent monitors the primary Cisco MDS documentation URL:
- **Primary URL**: https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html
- **Schedule**: Weekly automated checks for document updates
- **Storage**: Downloads PDFs to `knowledge_source/` with proper naming and revision control
- **Tracking**: Maintains metadata (date, size, SHA256 checksum) in SQLite database
- **RAG Ready**: Prepared documents for Retrieval-Augmented Generation

## Key Features

- **Autonomous Operation**: Weekly scheduled runs to detect and download new/updated PDFs
- **Metadata Repository**: SQLite database tracking download date, file size, SHA256 checksums
- **Revision Control**: Archives old versions when updates detected, maintains history in `knowledge_source/archive/`
- **One-Time URLs**: Support for manually added URLs via configuration
- **Test Automation**: Auto-updating test plans when code changes are made
- **RAG Integration**: Document preparation for vector database and retrieval systems

## Quick Start

1. **Setup Environment**
   ```bash
   git clone <repo-url>
   cd mds_knowledge_capture
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Agent**
   - Set up `.env` file with LangSmith API keys
   - Review `config/agent_config.json` for scheduling and URL settings

3. **Run Agent**
   ```bash
   # One-time run
   python src/agent.py

   # Enable weekly scheduling
   python src/scheduler.py
   ```

4. **View Documentation**
   ```bash
   # Open in VSCode
   code docs/project_plan.md
   ```

## Project Structure

```
mds_knowledge_capture/
├── src/                    # Core agent implementation
│   ├── agent.py           # Main LangGraph agent
│   ├── scraper.py         # Web scraping and PDF download
│   ├── metadata.py        # SQLite metadata management
│   ├── revision_control.py # Document versioning
│   └── rag_prep.py        # RAG document preparation
├── knowledge_source/       # PDF storage with revision control
│   ├── current/           # Latest versions
│   └── archive/           # Historical versions by date
├── config/                # Configuration files
│   ├── agent_config.json  # Agent settings and schedules
│   └── one_time_urls.json # Additional URLs to process
├── docs/                  # Documentation and auto-generated plans
│   ├── project_plan.md    # Detailed implementation plan
│   ├── test_plan.md       # Auto-updating test documentation
│   └── architecture.md    # System design documentation
├── tests/                 # Comprehensive test suite
│   ├── unit/             # Unit tests for individual components
│   ├── integration/      # Integration tests for agent workflows
│   └── e2e/              # End-to-end RAG testing
├── .vscode/              # VSCode configuration for development
└── requirements.txt      # Python dependencies
```

## Technology Stack

- **Agent Framework**: LangGraph for stateful agent orchestration
- **AI Integration**: LangChain for document processing and RAG chains
- **Monitoring**: LangSmith for agent tracing and performance monitoring
- **Storage**: SQLite for metadata, Git LFS for large PDF files
- **Scheduling**: APScheduler for weekly automated runs
- **Testing**: pytest with automated test plan generation

## Development Workflow

1. **Follow the Plan**: Use VSCode to open `docs/project_plan.md` and track progress
2. **Run Tasks**: Use VSCode tasks (Ctrl+Shift+P → "Tasks: Run Task")
   - "Run Agent" - Execute the agent
   - "Run Tests" - Execute test suite
   - "Update Docs" - Regenerate documentation
3. **Track Changes**: Git commits trigger automatic test plan and documentation updates

## Next Steps

See `docs/project_plan.md` for detailed implementation steps and checklists to follow.

---

## GitHub Configuration

To update your GitHub information for git, run the following commands in your terminal:

```bash
git config --global user.name "Jason Mooney"
git config --global user.email "github@jasonmooney.com"
git config --global github.user "jasonmooney"
```

Replace `"Your Name"`, `"your.email@example.com"`, and `"your-github-username"` with your actual GitHub account details.

---

## Validation Summary

This plan matches the original request:

- **Primary URL Monitoring**: Agent scrapes the Cisco documentation site and tracks all linked documents.
- **PDF Download & Naming**: Downloads PDFs, names them appropriately, and stores in `knowledge_source/`.
- **Metadata Tracking**: Maintains download date, file size, and SHA256 checksum in a SQLite repository.
- **Weekly Update Checks**: Scheduled weekly runs to detect and process document changes.
- **Revision Control**: Archives older documents and maintains only the latest in the main directory.
- **One-Time URLs**: Supports adding extra URLs via configuration for one-time processing.
- **Documentation**: All docs and plans are maintained in the `./docs` directory.
- **Test Plan**: Automated test plan and documentation updates are included.
- **RAG Integration**: Documents are prepared for retrieval-augmented generation workflows.
- **AI Technologies**: Uses LangChain, LangGraph, and LangSmith as requested.
- **Best Practices**: Follows modular coding, version control, and automation standards.

All requirements from the original prompt are addressed in this plan.
