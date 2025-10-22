"""
Load company documents into the RAG system
"""
import sys
import asyncio
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import add_document, init_db
from agents.rag_agent import RAGAgent
from loguru import logger


async def load_document_file(file_path: Path, doc_type: str, rag_agent: RAGAgent):
    """Load a single document file"""
    try:
        logger.info(f"Loading document: {file_path.name}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add to database
        doc = add_document(
            title=file_path.stem,
            doc_type=doc_type,
            file_path=str(file_path),
            content=content
        )
        
        # Index in vector database
        result = await rag_agent.index_document(
            doc_id=doc.id,
            title=doc.title,
            content=content,
            doc_type=doc_type
        )
        
        if result["success"]:
            logger.success(f"Loaded: {doc.title}")
            return True
        else:
            logger.error(f"Failed to index: {doc.title}")
            return False
            
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        return False


async def load_documents_from_directory(directory: Path, rag_agent: RAGAgent):
    """Load all documents from a directory"""
    
    # Document type mapping
    type_mapping = {
        'manual': ['manual', 'guide', 'handbook'],
        'sop': ['sop', 'procedure', 'process'],
        'policy': ['policy', 'rule', 'regulation']
    }
    
    # Find all text files
    text_files = list(directory.glob('**/*.txt')) + list(directory.glob('**/*.md'))
    
    if not text_files:
        logger.warning(f"No .txt or .md files found in {directory}")
        return
    
    logger.info(f"Found {len(text_files)} documents to load")
    
    success_count = 0
    for file_path in text_files:
        # Determine document type from filename
        filename_lower = file_path.name.lower()
        doc_type = 'manual'  # default
        
        for dtype, keywords in type_mapping.items():
            if any(keyword in filename_lower for keyword in keywords):
                doc_type = dtype
                break
        
        success = await load_document_file(file_path, doc_type, rag_agent)
        if success:
            success_count += 1
    
    logger.success(f"Loaded {success_count}/{len(text_files)} documents successfully")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Load documents into RAG system')
    parser.add_argument('--path', type=str, default='./data/documents',
                       help='Path to documents directory')
    
    args = parser.parse_args()
    doc_path = Path(args.path)
    
    if not doc_path.exists():
        logger.error(f"Directory not found: {doc_path}")
        print(f"❌ Directory not found: {doc_path}")
        print("\nCreate the directory and add your company documents:")
        print(f"  mkdir -p {doc_path}")
        print(f"  # Add .txt or .md files to {doc_path}")
        return
    
    try:
        # Initialize database
        init_db()
        
        # Create a mock bot object for RAG agent
        class MockBot:
            async def send_message(self, chat_id, text):
                pass
        
        # Initialize RAG agent
        rag_agent = RAGAgent(MockBot())
        
        # Load documents
        await load_documents_from_directory(doc_path, rag_agent)
        
        # Show statistics
        stats = rag_agent.get_collection_stats()
        print(f"\n✅ Document loading completed!")
        print(f"Total chunks indexed: {stats['total_chunks']}")
        
    except Exception as e:
        logger.error(f"Failed to load documents: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
