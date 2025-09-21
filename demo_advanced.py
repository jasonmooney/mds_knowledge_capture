"""
Quick demo script for the Advanced MDS Agent interactive features
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Demo the advanced agent capabilities."""
    
    print("🚀 Advanced MDS Knowledge Capture Agent Demo")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    
    print(f"📁 Working directory: {current_dir}")
    print(f"📄 Python version: {sys.version}")
    
    # Check if vector database exists
    chroma_db_path = current_dir / "chroma_db"
    if chroma_db_path.exists():
        print(f"✅ Vector database found at: {chroma_db_path}")
        
        # Check the size of the database
        total_size = sum(f.stat().st_size for f in chroma_db_path.rglob('*') if f.is_file())
        print(f"📊 Database size: {total_size / (1024*1024):.1f} MB")
    else:
        print("❌ Vector database not found - run complete cycle first")
        return
    
    # Test some sample questions
    sample_questions = [
        "What is fabric binding?",
        "How to configure trunk ports?",
        "List MDS troubleshooting commands"
    ]
    
    print("\\n🤔 Testing sample questions:")
    print("-" * 40)
    
    for i, question in enumerate(sample_questions, 1):
        print(f"\\n{i}. {question}")
        
        try:
            # Run the advanced agent
            cmd = [
                sys.executable, 
                "src/agent_advanced.py", 
                "--mode", "question",
                "--question", question,
                "--log-level", "WARNING"  # Reduce noise
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Extract the answer from output
                output_lines = result.stdout.strip().split('\\n')
                for line in output_lines:
                    if line.startswith('💡 Answer:'):
                        answer = line[11:].strip()  # Remove "💡 Answer: "
                        # Truncate long answers
                        if len(answer) > 200:
                            answer = answer[:200] + "..."
                        print(f"   💡 {answer}")
                        break
                else:
                    print("   ❌ Could not extract answer")
            else:
                print(f"   ❌ Error (code {result.returncode})")
                if result.stderr:
                    print(f"   📝 {result.stderr.strip()[:100]}...")
                    
        except subprocess.TimeoutExpired:
            print("   ⏱️  Timeout")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    print("\\n🎯 Demo completed!")
    print("\\nTo try interactive mode, run:")
    print("   python src/agent_advanced.py --mode interactive")
    

if __name__ == "__main__":
    main()