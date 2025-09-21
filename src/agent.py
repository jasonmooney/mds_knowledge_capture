"""
Main MDS Knowledge Capture Agent using LangGraph.
Orchestrates web scraping, document processing, and revision control.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Annotated
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langsmith import traceable

from src.metadata import MetadataManager
from src.scraper import MDSDocumentScraper
from src.revision_control import RevisionController

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the MDS Knowledge Capture Agent."""
    messages: Annotated[List[Dict], "Messages in the conversation"]
    config: Dict
    urls: List[str]
    discovered_pdfs: List[Dict]
    downloaded_docs: List[Dict]
    processed_docs: List[Dict]
    errors: List[str]
    status: str
    run_id: str


class MDSKnowledgeCaptureAgent:
    """LangGraph-based agent for MDS documentation capture."""
    
    def __init__(self, config_path: str = "config/agent_config.json"):
        """Initialize the agent with configuration."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize components
        self.metadata_manager = MetadataManager(self.config["storage"]["database_path"])
        self.scraper = MDSDocumentScraper(
            user_agent=self.config["download"]["user_agent"],
            timeout=self.config["download"]["timeout_seconds"],
            max_concurrent=self.config["download"]["max_concurrent"]
        )
        self.revision_controller = RevisionController(
            current_path=self.config["storage"]["current_path"],
            archive_path=self.config["storage"]["archive_path"],
            metadata_manager=self.metadata_manager
        )
        
        # Initialize LLM with Mistral via OpenRouter
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            logger.error("OPENROUTER_API_KEY not found!")
            logger.info("🔧 Setup required:")
            logger.info("   1. Get free API key at: https://openrouter.ai/")
            logger.info("   2. Run: python setup_mistral.py")
            logger.info("   3. Set: export OPENROUTER_API_KEY='your_key'")
            raise ValueError("OpenRouter API key required for Mistral LLM")
        
        try:
            self.llm = ChatOpenAI(
                model="mistralai/mistral-small-3.2-24b-instruct:free",
                temperature=0.1,
                openai_api_key=openrouter_api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                model_kwargs={
                    "extra_headers": {
                        "HTTP-Referer": "https://github.com/jasonmooney/mds_knowledge_capture",
                        "X-Title": "MDS Knowledge Capture Agent"
                    }
                }
            )
            logger.info("Mistral Small 3.2 24B initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral LLM: {e}")
            logger.info("💡 Try running: python setup_mistral.py")
            raise
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info("MDS Knowledge Capture Agent initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        
        # Ensure log directory exists
        log_file = log_config.get("file", "logs/agent.log")
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config.get("level", "INFO")),
            format=log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def analyze_urls(self, state: AgentState) -> AgentState:
        """Analyze and prepare URLs for processing."""
        urls = []
        
        # Add primary URL
        primary_url = state["config"].get("primary_url")
        if primary_url:
            urls.append(primary_url)
        
        # Load one-time URLs
        try:
            with open("config/one_time_urls.json", 'r') as f:
                one_time_config = json.load(f)
                
            for url_info in one_time_config.get("one_time_urls", []):
                if not url_info.get("processed", False):
                    urls.append(url_info["url"])
        
        except Exception as e:
            logger.warning(f"Could not load one-time URLs: {e}")
        
        state["urls"] = urls
        state["status"] = "urls_prepared"
        
        logger.info(f"Prepared {len(urls)} URLs for processing")
        return state
    
    def scrape_documents(self, state: AgentState) -> AgentState:
        """Scrape URLs and discover PDF documents with intelligent roadmap traversal."""
        discovered_pdfs = []
        
        # Check if primary URL is the roadmap - use intelligent discovery
        roadmap_url = "https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html"
        
        if roadmap_url in state["urls"]:
            logger.info("Using intelligent roadmap discovery")
            try:
                # Use enhanced discovery from roadmap
                roadmap_pdfs = self.scraper.discover_documents_from_roadmap(roadmap_url)
                discovered_pdfs.extend(roadmap_pdfs)
                logger.info(f"Intelligent discovery found {len(roadmap_pdfs)} unique documents")
                
                # Remove roadmap URL from regular processing
                remaining_urls = [url for url in state["urls"] if url != roadmap_url]
            except Exception as e:
                error_msg = f"Error in intelligent roadmap discovery: {str(e)}"
                state["errors"].append(error_msg)
                logger.error(error_msg)
                remaining_urls = state["urls"]  # Fallback to all URLs
        else:
            remaining_urls = state["urls"]
        
        # Process any remaining URLs with standard scraping
        for url in remaining_urls:
            try:
                logger.info(f"Scraping {url}")
                soup = self.scraper.fetch_page(url)
                
                if soup:
                    pdf_links = self.scraper.extract_pdf_links(soup, url)
                    discovered_pdfs.extend(pdf_links)
                    logger.info(f"Found {len(pdf_links)} PDFs on {url}")
                else:
                    error_msg = f"Failed to fetch {url}"
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"Error scraping {url}: {str(e)}"
                state["errors"].append(error_msg)
                logger.error(error_msg)
        
        state["discovered_pdfs"] = discovered_pdfs
        state["status"] = "documents_discovered"
        
        logger.info(f"Total PDFs discovered: {len(discovered_pdfs)}")
        return state
    
    def download_documents(self, state: AgentState) -> AgentState:
        """Download discovered PDF documents."""
        download_path = Path(state["config"]["storage"]["current_path"]).parent / "downloads"
        download_path.mkdir(parents=True, exist_ok=True)
        
        try:
            downloaded_docs = []
            
            # Download each PDF individually
            for pdf_info in state["discovered_pdfs"]:
                try:
                    result = asyncio.run(self.scraper.download_pdf(pdf_info, str(download_path)))
                    if result:
                        downloaded_docs.append(result)
                except Exception as e:
                    error_msg = f"Error downloading {pdf_info['url']}: {str(e)}"
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
            
            state["downloaded_docs"] = downloaded_docs
            state["status"] = "documents_downloaded"
            
            logger.info(f"Successfully downloaded {len(downloaded_docs)} documents")
            
        except Exception as e:
            error_msg = f"Download process failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            state["status"] = "download_failed"
        
        return state
    
    def process_revisions(self, state: AgentState) -> AgentState:
        """Process documents with revision control."""
        try:
            processed_docs = self.revision_controller.process_documents(state["downloaded_docs"])
            
            state["processed_docs"] = processed_docs
            state["status"] = "processing_complete"
            
            logger.info(f"Successfully processed {len(processed_docs)} documents with revision control")
            
        except Exception as e:
            error_msg = f"Revision processing failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            state["status"] = "processing_failed"
        
        return state
    
    def analyze_results(self, state: AgentState) -> str:
        """Analyze results and generate summary using LLM."""
        try:
            # Prepare context for LLM
            urls_processed = len(state.get("urls", []))
            pdfs_discovered = len(state.get("discovered_pdfs", []))
            docs_downloaded = len(state.get("downloaded_docs", []))
            docs_processed = len(state.get("processed_docs", []))
            errors = state.get("errors", [])
            
            context = f"""
            MDS Knowledge Capture Agent Execution Summary:
            - URLs processed: {urls_processed}
            - PDFs discovered: {pdfs_discovered}
            - Documents downloaded: {docs_downloaded}
            - Documents processed with revision control: {docs_processed}
            - Errors encountered: {len(errors)}
            
            Processing Status: {state.get("status", "unknown")}
            
            Errors:
            {chr(10).join(errors) if errors else "None"}
            
            Downloaded Documents:
            """
            
            for doc in state.get("downloaded_docs", []):
                context += f"\\n- {doc.get('filename', 'Unknown')}: {doc.get('file_size', 0)} bytes"
            
            for doc in state.get("processed_docs", []):
                update_status = " (UPDATE)" if doc.get("is_update") else " (NEW)"
                context += f"\\n- Processed: {Path(doc.get('current_file_path', '')).name}{update_status}"
            
            # Ask LLM to analyze and summarize
            messages = [
                SystemMessage(content="""You are an AI assistant analyzing the results of a document capture agent. 
                Provide a clear, concise summary of the execution results, highlighting successes, issues, and recommendations."""),
                HumanMessage(content=context)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return f"Analysis failed: {str(e)}"
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_urls", self.analyze_urls)
        workflow.add_node("scrape_documents", self.scrape_documents)
        workflow.add_node("download_documents", self.download_documents)
        workflow.add_node("process_revisions", self.process_revisions)
        
        # Add edges
        workflow.add_edge(START, "analyze_urls")
        workflow.add_edge("analyze_urls", "scrape_documents")
        workflow.add_edge("scrape_documents", "download_documents")
        workflow.add_edge("download_documents", "process_revisions")
        workflow.add_edge("process_revisions", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_urls")
        
        return workflow.compile()
    
    @traceable
    def run(self) -> Dict:
        """Execute the agent workflow."""
        run_id = f"mds_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize state
        initial_state = {
            "messages": [],
            "config": self.config,
            "urls": [],
            "discovered_pdfs": [],
            "downloaded_docs": [],
            "processed_docs": [],
            "errors": [],
            "status": "starting",
            "run_id": run_id
        }
        
        logger.info(f"Starting MDS Knowledge Capture Agent run: {run_id}")
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Generate analysis
            analysis = self.analyze_results(final_state)
            final_state["analysis"] = analysis
            
            logger.info(f"Agent run completed: {run_id}")
            logger.info(f"Final status: {final_state['status']}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            return {
                **initial_state,
                "status": "failed",
                "errors": [str(e)],
                "analysis": f"Agent execution failed: {str(e)}"
            }


def main():
    """Main entry point for the agent."""
    try:
        agent = MDSKnowledgeCaptureAgent()
        result = agent.run()
        
        print("\n" + "="*60)
        print("MDS KNOWLEDGE CAPTURE AGENT - EXECUTION SUMMARY")
        print("="*60)
        print(f"Run ID: {result['run_id']}")
        print(f"Status: {result['status']}")
        print(f"URLs Processed: {len(result.get('urls', []))}")
        print(f"PDFs Discovered: {len(result.get('discovered_pdfs', []))}")
        print(f"Documents Downloaded: {len(result.get('downloaded_docs', []))}")
        print(f"Documents Processed: {len(result.get('processed_docs', []))}")
        print(f"Errors: {len(result.get('errors', []))}")
        
        if result.get('analysis'):
            print("\nAI Analysis:")
            print(result['analysis'])
        
        if result.get('errors'):
            print("\nErrors Encountered:")
            for error in result['errors']:
                print(f"• {error}")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nAgent execution interrupted by user")
    except Exception as e:
        print(f"\nAgent execution failed: {e}")
        logger.error(f"Main execution failed: {e}")


if __name__ == "__main__":
    main()