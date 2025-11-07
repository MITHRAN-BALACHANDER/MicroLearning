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
        print(f"  📄 Processing: {file_path.name}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_length = len(content)
        print(f"     📊 Size: {content_length:,} characters")
        
        # Add to database
        doc = add_document(
            title=file_path.stem,
            doc_type=doc_type,
            file_path=str(file_path),
            content=content
        )
        
        print(f"     💾 Database ID: {doc.id}")
        
        # Index in vector database
        result = await rag_agent.index_document(
            doc_id=doc.id,
            title=doc.title,
            content=content,
            doc_type=doc_type
        )
        
        if result["success"]:
            chunks = result.get("chunks", 0)
            print(f"     ✅ Indexed: {chunks} chunks created")
            logger.success(f"Loaded: {doc.title} ({chunks} chunks)")
            return True, chunks
        else:
            print(f"     ❌ Failed to index")
            logger.error(f"Failed to index: {doc.title}")
            return False, 0
            
    except Exception as e:
        print(f"     ❌ Error: {str(e)}")
        logger.error(f"Error loading {file_path}: {str(e)}")
        return False, 0


async def load_documents_from_directory(directory: Path, rag_agent: RAGAgent):
    """Load all documents from a directory"""
    
    # Document type mapping
    type_mapping = {
        'manual': ['manual', 'guide', 'handbook', 'employee'],
        'sop': ['sop', 'procedure', 'process', 'support'],
        'policy': ['policy', 'rule', 'regulation', 'work']
    }
    
    # Find all text files
    text_files = list(directory.glob('**/*.txt')) + list(directory.glob('**/*.md'))
    
    if not text_files:
        logger.warning(f"No .txt or .md files found in {directory}")
        print(f"⚠️  No .txt or .md files found in {directory}")
        return
    
    logger.info(f"Found {len(text_files)} documents to load")
    print(f"📚 Found {len(text_files)} document(s) to process\n")
    
    success_count = 0
    total_chunks = 0
    
    for idx, file_path in enumerate(text_files, 1):
        print(f"[{idx}/{len(text_files)}]")
        
        # Determine document type from filename
        filename_lower = file_path.name.lower()
        doc_type = 'manual'  # default
        
        for dtype, keywords in type_mapping.items():
            if any(keyword in filename_lower for keyword in keywords):
                doc_type = dtype
                break
        
        print(f"     📂 Type: {doc_type}")
        
        success, chunks = await load_document_file(file_path, doc_type, rag_agent)
        if success:
            success_count += 1
            total_chunks += chunks
        
        print()  # Empty line between files
    
    print("=" * 60)
    print(f"✅ Successfully loaded: {success_count}/{len(text_files)} documents")
    print(f"📊 Total chunks created: {total_chunks}")
    logger.success(f"Loaded {success_count}/{len(text_files)} documents successfully ({total_chunks} chunks)")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Load documents into RAG system')
    parser.add_argument('--path', type=str, default='../data/documents',
                       help='Path to documents directory')
    
    args = parser.parse_args()
    
    # Resolve path relative to script location
    script_dir = Path(__file__).parent
    doc_path = (script_dir / args.path).resolve()
    
    if not doc_path.exists():
        logger.error(f"Directory not found: {doc_path}")
        print(f"\n❌ Directory not found: {doc_path}")
        print("\nCreate the directory and add your company documents:")
        print(f"  mkdir {doc_path}")
        print(f"  # Add .txt or .md files to {doc_path}")
        return
    
    print(f"\n📂 Loading documents from: {doc_path}")
    print(f"📍 Absolute path: {doc_path.absolute()}\n")
    
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
        print("\n" + "=" * 60)
        print("📊 FINAL STATISTICS")
        print("=" * 60)
        print(f"✅ Total chunks in database: {stats.get('total_chunks', 0)}")
        print(f"✅ Status: {stats.get('status', 'unknown')}")
        print(f"✅ Vector database: ChromaDB")
        print(f"✅ Collection: company_docs")
        print("=" * 60)
        print("\n🎉 Document loading completed successfully!")
        print("\n💡 You can now use the RAG agent to query these documents:")
        print("   - Start the bot: python main.py")
        print("   - Use /ask command to query documents")
        print("   - Example: /ask What is the remote work policy?\n")
        
    except Exception as e:
        logger.error(f"Failed to load documents: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
