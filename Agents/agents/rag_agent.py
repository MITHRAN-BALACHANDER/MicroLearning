"""
RAG Agent - Retrieval Augmented Generation for company manuals and SOPs
"""
from typing import Dict, Any, List, Optional
import os
import asyncio
from loguru import logger
import google.generativeai as genai
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from database.operations import get_active_documents, get_user_by_telegram_id
from config.settings import (
    GEMINI_API_KEY, 
    CHROMA_PERSIST_DIRECTORY, 
    RAG_AGENT_PROMPT
)


class RAGAgent:
    """
    Dynamic agent responsible for:
    - Managing company documentation (manuals, SOPs)
    - Answering questions using RAG
    - Providing sourced, accurate information
    - Document retrieval and summarization
    """
    
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.name = "RAGAgent"
        self.description = "Provides information from company documents"
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Initialize ChromaDB with persistence
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="company_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.active_queries = {}
        logger.info(f"Initialized {self.name} with ChromaDB")
    
    async def index_document(self, doc_id: int, title: str, content: str, 
                            doc_type: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Index a document into the vector database
        
        Args:
            doc_id: Document ID
            title: Document title
            content: Document content
            doc_type: Type of document (manual, sop, policy)
            metadata: Additional metadata
            
        Returns:
            Dict with indexing status
        """
        try:
            # Split content into chunks
            chunks = self._chunk_text(content, chunk_size=500, overlap=50)
            
            # Prepare data for ChromaDB
            ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
            embeddings = self.embedding_model.encode(chunks).tolist()
            metadatas = [
                {
                    "doc_id": doc_id,
                    "title": title,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    **(metadata or {})
                }
                for i in range(len(chunks))
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
            logger.info(f"Indexed document {doc_id} ({title}) with {len(chunks)} chunks")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks": len(chunks),
                "message": f"Document '{title}' indexed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def query_documents(self, query: str, telegram_id: str, 
                             n_results: int = 5) -> Dict[str, Any]:
        """
        Query the document database and generate an answer
        
        Args:
            query: User's question
            telegram_id: User's Telegram ID
            n_results: Number of similar chunks to retrieve
            
        Returns:
            Dict with answer and sources
        """
        try:
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Track query
            self.active_queries[telegram_id] = {
                "query": query,
                "timestamp": None
            }
            
            # Encode query
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {
                    "success": True,
                    "answer": "I couldn't find any relevant information in the company documents. "
                             "Please try rephrasing your question or contact HR for assistance.",
                    "sources": []
                }
            
            # Prepare context from retrieved chunks (limit to top 3 for brevity)
            context_chunks = results['documents'][0][:3]  # Limit to top 3 chunks
            metadatas = results['metadatas'][0][:3]
            
            context = "\n\n".join([
                f"Document: {meta['title']}\n{doc[:500]}"  # Limit each chunk to 500 chars
                for doc, meta in zip(context_chunks, metadatas)
            ])
            
            # Generate answer using Gemini with simpler prompt
            prompt = f"""Answer this question based on the company documents provided.

Company Documents:
{context}

Question: {query}

Provide a clear answer citing the source documents."""
            
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Configure safety settings to be less restrictive
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={'temperature': 0.3, 'max_output_tokens': 800},
                safety_settings=safety_settings
            )
            
            # Check if response was blocked or has no text
            answer = None
            try:
                if response and response.text:
                    answer = response.text
            except (ValueError, AttributeError) as e:
                logger.warning(f"Could not get response text: {str(e)}")
                # Try to get feedback
                if hasattr(response, 'prompt_feedback'):
                    logger.warning(f"Response feedback: {response.prompt_feedback}")
                if hasattr(response, 'candidates') and response.candidates:
                    logger.warning(f"Finish reason: {response.candidates[0].finish_reason}")
            
            # If no answer from AI, provide fallback with document excerpts
            if not answer:
                logger.info("Using fallback answer with document excerpts")
                answer = "Based on the company documents, here's what I found:\n\n"
                answer += "\n\n".join([f"From {meta['title']}:\n{doc[:300]}..." 
                                      for doc, meta in zip(context_chunks, metadatas)])
                answer += "\n\n(Note: Full AI-generated answer was blocked. Please rephrase your question or contact support.)"
            
            # Extract unique sources
            sources = list(set([
                f"{meta['title']} ({meta['doc_type']})"
                for meta in metadatas
            ]))
            
            # Escape markdown special characters in answer
            def escape_markdown(text):
                """Escape special characters for Telegram MarkdownV2"""
                # For Markdown mode (not MarkdownV2), we need to escape _ * [ ] ( ) ~ ` > # + - = | { } . !
                # But simpler: just remove problematic bold/italic markers
                return text.replace('*', '').replace('_', '').replace('`', '')
            
            # Format message without markdown formatting to avoid parsing errors
            message_text = (
                f"Answer:\n\n{escape_markdown(answer)}\n\n"
                f"───────────\n"
                f"Sources:\n" + "\n".join([f"- {s}" for s in sources])
            )
            
            # Send answer to user (without parse_mode to avoid markdown errors)
            try:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message_text
                )
                logger.info(f"Answered query for user {telegram_id}")
            except Exception as send_error:
                logger.error(f"Error sending message: {str(send_error)}")
                # Return the answer even if sending fails
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources,
                "chunks_used": len(context_chunks),
                "message": message_text
            }
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def summarize_document(self, doc_id: int, telegram_id: str) -> Dict[str, Any]:
        """
        Provide a summary of a specific document
        
        Args:
            doc_id: Document ID
            telegram_id: User's Telegram ID
            
        Returns:
            Dict with summary
        """
        try:
            # Retrieve all chunks for the document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if not results['documents']:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            # Combine chunks
            full_content = "\n".join(results['documents'])
            doc_title = results['metadatas'][0]['title']
            doc_type = results['metadatas'][0]['doc_type']
            
            # Generate summary
            prompt = f"""
            Provide a comprehensive summary of this {doc_type} document:
            
            Title: {doc_title}
            
            Content:
            {full_content[:4000]}  # Limit content size
            
            Include:
            1. Main purpose and scope
            2. Key points and procedures
            3. Important requirements or guidelines
            4. Who should use this document
            """
            
            full_prompt = f"{RAG_AGENT_PROMPT}\n\n{prompt}"
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config={'temperature': 0.3, 'max_output_tokens': 800}
            )
            
            summary = response.text
            
            # Send summary
            await self.bot.send_message(
                chat_id=telegram_id,
                text=f"Document Summary\n\n"
                     f"Title: {doc_title}\n"
                     f"Type: {doc_type}\n\n"
                     f"{summary}"
            )
            
            return {
                "success": True,
                "summary": summary,
                "doc_title": doc_title
            }
            
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def list_available_documents(self, telegram_id: str) -> Dict[str, Any]:
        """
        List all available documents in the system
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            Dict with document list
        """
        try:
            documents = get_active_documents()
            
            if not documents:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text="No documents are currently available in the system."
                )
                return {"success": True, "documents": []}
            
            # Group by type
            docs_by_type = {}
            for doc in documents:
                if doc.doc_type not in docs_by_type:
                    docs_by_type[doc.doc_type] = []
                docs_by_type[doc.doc_type].append(doc)
            
            # Format message
            message = "Available Documents\n\n"
            
            for doc_type, docs in docs_by_type.items():
                message += f"{doc_type.upper()}:\n"
                for doc in docs:
                    message += f"  - {doc.title} (ID: {doc.id})\n"
                message += "\n"
            
            message += "Use `/ask [your question]` to search these documents!"
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message
            )
            
            return {
                "success": True,
                "documents": [
                    {"id": d.id, "title": d.title, "type": d.doc_type}
                    for d in documents
                ]
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for period, question mark, or exclamation
                for i in range(end, start + chunk_size // 2, -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return chunks
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "name": self.name,
            "active_queries": len(self.active_queries),
            "collection_stats": self.get_collection_stats(),
            "status": "active"
        }
