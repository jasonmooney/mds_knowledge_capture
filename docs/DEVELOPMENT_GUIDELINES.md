# 🚨 MDS Knowledge Capture - Development Guidelines

## **MANDATORY ARCHITECTURE RULES**

### ❌ **FORBIDDEN PRACTICES**
1. **NO Python files in root directory** (main project folder)
2. **NO enhanced_*.py duplicate files**  
3. **NO separate agent files when src/agent.py exists**
4. **NO bypassing the src/ directory structure**
5. **NO creating new classes when existing ones can be enhanced**
6. **NO global pip installs** - ALWAYS use virtual environment

### ✅ **REQUIRED PRACTICES**
1. **ENHANCE existing files** in src/ directory:
   - `src/scraper.py` - Add methods to `MDSDocumentScraper` class
   - `src/agent.py` - Add methods to `MDSKnowledgeAgent` class  
   - `src/metadata.py` - Add methods to existing metadata classes
   - `src/revision_control.py` - Add methods to existing revision classes
   - `src/rag_prep.py` - Add methods to existing RAG classes

2. **FOLLOW established import patterns:**
   ```python
   from src.scraper import MDSDocumentScraper
   from src.agent import MDSKnowledgeAgent
   from src.metadata import DocumentMetadata
   ```

3. **MAINTAIN the LangGraph workflow** in `src/agent.py`

4. **ALWAYS use virtual environment for Python operations:**
   - Use `.\venv\Scripts\pip.exe install <package>` (Windows)
   - Use `.\venv\Scripts\python.exe <script>` (Windows)
   - Use `./venv/bin/pip install <package>` (Unix/Linux)
   - Use `./venv/bin/python <script>` (Unix/Linux)
   - NEVER use global pip install when venv exists

5. **DOCUMENT all changes** in `CHANGE.md` with proper format

## **DIRECTORY STRUCTURE (IMMUTABLE)**

```
mds_knowledge_capture/
├── src/                    # ✅ ALL PYTHON CLASSES HERE
│   ├── agent.py           # Main LangGraph agent
│   ├── scraper.py         # Document scraper  
│   ├── metadata.py        # Metadata management
│   ├── revision_control.py # Version control
│   └── rag_prep.py        # RAG processing
├── config/                # Configuration files only
├── scripts/               # Utility scripts and validation  
├── docs/                  # Documentation
├── knowledge_source/      # Downloaded documents
├── chroma_db/            # Vector database
└── [ROOT]                # ❌ NO PYTHON FILES HERE
    ├── .env              # ✅ Config files OK
    ├── requirements.txt  # ✅ Config files OK
    └── README.md         # ✅ Documentation OK
```

## **PYTHON ENVIRONMENT MANAGEMENT**

### 🐍 **VIRTUAL ENVIRONMENT RULES**

**MANDATORY:** Always use the project's virtual environment for all Python operations.

#### ✅ **CORRECT Commands:**
```powershell
# Windows PowerShell
.\venv\Scripts\pip.exe install <package>
.\venv\Scripts\python.exe <script.py>
.\venv\Scripts\python.exe -m <module>
```

```bash
# Unix/Linux/macOS
./venv/bin/pip install <package>
./venv/bin/python <script.py>
./venv/bin/python -m <module>
```

#### ❌ **FORBIDDEN Commands:**
```powershell
pip install <package>          # Pollutes global environment
python <script.py>             # May use wrong Python version
pip uninstall <package>        # Removes from wrong environment
```

#### 🔍 **Detection of Virtual Environment:**
Before ANY pip install, check for:
- `venv/` directory in project root
- `.venv/` directory in project root  
- VSCode tasks using `.\venv\Scripts\python.exe`
- `requirements.txt` file (indicates managed dependencies)

#### 🧹 **Environment Cleanup:**
If global packages were accidentally installed:
```powershell
pip list --user                    # Check what was polluted
pip uninstall -y <package-list>    # Clean up the mess
```

### 📋 **PRE-OPERATION CHECKLIST**
Before ANY Python command:
1. ☐ Check if virtual environment exists
2. ☐ Use full path to venv pip/python
3. ☐ Verify command targets the venv, not global
4. ☐ Test in venv first before assuming success

## **ENHANCEMENT PATTERNS**

### ✅ **CORRECT: Add method to existing class**
```python
# In src/scraper.py
class MDSDocumentScraper:
    # ... existing methods ...
    
    def discover_documents_from_roadmap(self, roadmap_url: str) -> List[Dict]:
        """NEW METHOD: Discover documents intelligently"""
        # Implementation here
        pass
```

### ❌ **WRONG: Create duplicate file**
```python
# DON'T CREATE: enhanced_scraper.py
class EnhancedMDSDocumentScraper:  # This is FORBIDDEN
    pass
```

## **VSCODE ENFORCEMENT**

The `.vscode/settings.json` file enforces these rules by:
- Excluding `enhanced_*.py` files from explorer
- Hiding duplicate patterns in search
- Setting up proper Python linting
- Configuring import checking

## **CHANGE TRACKING**

Every enhancement MUST be documented in `CHANGE.md`:

```markdown
## 2024-12-XX XX:XX:XX - jasmoone

### Prompt:
"Add intelligent document discovery to the scraper"

### Reasoning:
Enhanced existing MDSDocumentScraper class instead of creating new file

### Changed:
- Added discover_documents_from_roadmap() method to MDSDocumentScraper
- Integrated with existing async download functionality

### Modified Files:
- src/scraper.py (enhanced existing class)

### GitHub Commit Summary:
feat: Add intelligent document discovery to existing scraper class
```

## **PRE-DEVELOPMENT CHECKLIST**

Before making ANY code changes:

1. ☐ Identify which existing file in `src/` to enhance
2. ☐ Confirm the existing class to add methods to
3. ☐ Verify no duplicate functionality exists
4. ☐ Plan the enhancement approach (new methods, not new files)
5. ☐ Prepare the `CHANGE.md` entry format

## **VIOLATION CONSEQUENCES**

Creating files in the root directory or duplicate classes will result in:
1. Immediate cleanup requirement
2. Architectural violation documentation
3. Re-implementation using proper enhancement patterns

**Remember: ENHANCE, DON'T DUPLICATE!**