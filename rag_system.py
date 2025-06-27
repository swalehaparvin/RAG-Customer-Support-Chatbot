import os
from typing import List, Dict, Any
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.prompts import PromptTemplate

class CustomerSupportRAG:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
    def build_vector_store(self, documents: List[Document]):
        """Build vector store from documents"""
        
        # Create Chroma vector store
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        # Create retrieval QA chain
        self._setup_qa_chain()
    
    def _setup_qa_chain(self):
        """Setup the QA chain with custom prompt"""
        
        # Custom prompt template for customer support
        prompt_template = """You are a helpful AI customer support assistant. Use the following context to answer the customer's question. If you cannot find the answer in the context, politely say so and suggest contacting human support.

Context: {context}

Question: {question}

Instructions:
1. Provide accurate, helpful answers based only on the context
2. Be polite and professional
3. If uncertain, acknowledge the limitation
4. Suggest next steps when appropriate
5. Keep responses concise but complete

Answer:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create the chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.1, model_name="gpt-3.5-turbo"),
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
    
    def ask_question(self, question: str, model: str = "gpt-3.5-turbo", temperature: float = 0.1) -> Dict[str, Any]:
        """Ask a question and get an answer with sources"""
        
        if not self.qa_chain:
            raise ValueError("Vector store not built yet. Please process documents first.")
        
        # Update model if different
        if self.qa_chain.llm.model_name != model:
            self.qa_chain.llm = ChatOpenAI(temperature=temperature, model_name=model)
        
        # Get answer
        result = self.qa_chain({"question": question})
        
        # Extract sources
        sources = []
        for doc in result['source_documents']:
            source_info = f"📄 {doc.metadata.get('source', 'Unknown')} (Chunk {doc.metadata.get('chunk_index', 0)})"
            if doc.page_content:
                # Get first 150 characters as preview
                preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                source_info += f"\n💭 Preview: {preview}"
            sources.append(source_info)
        
        return {
            'answer': result['answer'],
            'sources': sources,
            'confidence': self._calculate_confidence(result)
        }
    
    def _calculate_confidence(self, result) -> float:
        """Calculate confidence score based on source relevance"""
        
        if not result['source_documents']:
            return 0.3
        
        # Simple heuristic: more sources = higher confidence
        num_sources = len(result['source_documents'])
        base_confidence = min(0.7 + (num_sources * 0.1), 0.95)
        
        return base_confidence
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge base"""
        
        if not self.vector_store:
            return {'doc_count': 0, 'chunk_count': 0}
        
        # Get collection info
        collection = self.vector_store._collection
        count = collection.count()
        
        # Estimate unique documents
        unique_sources = set()
        try:
            # Get a sample of metadata to count unique sources
            results = collection.get(limit=min(count, 100))
            for metadata in results['metadatas']:
                if metadata and 'source' in metadata:
                    unique_sources.add(metadata['source'])
        except:
            pass
        
        return {
            'doc_count': len(unique_sources) if unique_sources else 1,
            'chunk_count': count
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()