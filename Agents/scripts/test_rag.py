"""
Test RAG Agent - Verify document search is working
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.rag_agent import RAGAgent
from database.operations import init_db, get_or_create_user


class MockBot:
    """Mock Telegram bot for testing"""
    
    async def send_message(self, chat_id, text, parse_mode=None):
        """Mock send_message"""
        print(f"\n{'='*60}")
        print(f"📱 Message to {chat_id}:")
        print(f"{'='*60}")
        print(text)
        print(f"{'='*60}\n")
        return True


async def test_rag():
    """Test RAG agent functionality"""
    
    print("🔧 Initializing database...")
    init_db()
    
    print(" Creating mock bot...")
    mock_bot = MockBot()
    
    print("🧠 Initializing RAG Agent...")
    rag_agent = RAGAgent(mock_bot)
    
    # Check collection stats
    count = rag_agent.collection.count()
    print(f"  ChromaDB Collection Stats:")
    print(f"   Total chunks: {count}")
    
    if count == 0:
        print("\n⚠️  WARNING: No documents in ChromaDB!")
        print("   Run: python scripts/load_documents.py")
        return
    
    # Get a sample
    sample = rag_agent.collection.peek(limit=3)
    print(f"\n📄 Sample documents:")
    for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
        print(f"\n   {i+1}. {meta['title']} ({meta['doc_type']})")
        print(f"      {doc[:100]}...")
    
    # Create test user and get telegram_id (within session context)
    print("\n👤 Creating test user...")
    from database.operations import get_db
    with get_db() as db:
        test_user = get_or_create_user("TEST_123", "test_user", "Test", "User")
        test_telegram_id = str(test_user.telegram_id)  # Store as string before session closes
        print(f"   User created: {test_telegram_id}")
    
    # Test queries
    test_queries = [
        "What is the remote work policy?",
        "What are the working hours?",
        "How do I submit a support ticket?",
        "What is the vacation policy?"
    ]
    
    print(f"\n  Testing RAG queries...\n")
    
    for query in test_queries:
        print(f"\n{'─'*60}")
        print(f"❓ Query: {query}")
        print(f"{'─'*60}")
        
        try:
            result = await rag_agent.query_documents(query, test_telegram_id)
            
            if result["success"]:
                print(f"✅ Success!")
                print(f"   Chunks used: {result.get('chunks_used', 0)}")
                print(f"   Sources: {', '.join(result.get('sources', []))}")
                
                # The message should have been "sent" via mock bot
                
            else:
                print(f"❌ Failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ Test completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_rag())
