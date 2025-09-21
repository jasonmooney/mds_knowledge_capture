# Project Plan: MDS Knowledge Capture Agent

This plan outlines building an agentic agent for Cisco MDS docs. Follow in VSCode by opening this file and using the outline view.

## Overview
- **Goal**: Autonomous PDF downloads, metadata tracking, revision control, and RAG setup.
- **Tech Stack**: Python, LangChain/LangGraph, SQLite, Git.
- **Best Practices**: Modular code, tests, docs auto-updates via CI.

## Step-by-Step Plan
1. **Project Setup**
   - [ ] Initialize Git repo.
   - [ ] Create virtual env and `requirements.txt`.
   - [ ] Set up VSCode workspace (extensions: Python, GitLens).
   - Suggestion: Add `.env` for secrets.

2. **Agent Design**
   - [ ] Use LangGraph for stateful agent with tools (scraping, hashing).
   - [ ] Schedule weekly runs with APScheduler.
   - Question: Handle authentication?

3. **Web Scraping & Downloads**
   - [ ] Scrape primary URL: https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html
   - [ ] Download PDFs to `knowledge_source/`, rename (e.g., `mds_v9.0_2023-10-01.pdf`).
   - [ ] Add one-time URLs via `config/one_time_urls.json`.
   - Suggestion: Use async for efficiency.

4. **Metadata Tracking**
   - [ ] Store in SQLite: URL, filename, date, size, SHA256.
   - [ ] Compare checksums for changes.
   - Question: Prefer SQLite or JSON?

5. **Revision Control**
   - [ ] Archive old PDFs to `knowledge_source/archive/`.
   - [ ] Use Git LFS for large files.
   - Suggestion: Automate with scripts.

6. **RAG Integration**
   - [ ] Chunk PDFs with LangChain.
   - [ ] Store in ChromaDB.
   - Question: Specific model?

7. **Documentation & Testing**
   - [ ] Maintain in `docs/`.
   - [ ] Test plan: Unit (pytest), integration, E2E.
   - [ ] Auto-update via Git hooks.

8. **Deployment**
   - [ ] Dockerize.
   - [ ] Monitor with LangSmith.
   - Suggestion: Add health checks.

## Checklists & Tracking
- [ ] Complete each step and check off.
- [ ] Update this doc on changes.

## Suggestions
- Security: Use HTTPS.
- Efficiency: Parallel downloads.
- UI: Add Flask for status.

For code, see `src/`.
