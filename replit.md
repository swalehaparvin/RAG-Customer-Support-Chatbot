# AI Customer Support RAG System

## Overview

This is a Retrieval-Augmented Generation (RAG) based AI customer support system built with Streamlit and LangChain. The application allows users to upload documents (PDF, DOCX, TXT) and provides intelligent customer support responses based on the content of those documents. The system uses OpenAI's embeddings and language models to create a conversational AI assistant that can answer questions using context from uploaded documents.

## System Architecture

The application follows a modular architecture with three main components:

### Frontend Layer (Streamlit)
- **app.py**: Main Streamlit application providing the web interface
- Custom CSS styling for chat interface and UI components
- File upload functionality for knowledge base documents
- Chat interface for user-AI interactions

### Processing Layer
- **document_processor.py**: Handles document ingestion and text extraction
- **rag_system.py**: Implements the RAG pipeline with vector storage and retrieval

### Storage Layer
- Chroma vector database for document embeddings
- PostgreSQL database for persistent conversation history and document metadata
- Local file storage for uploaded documents
- Conversation memory for maintaining chat context

## Key Components

### Document Processing
- **Purpose**: Extract and chunk text from various document formats
- **Supported Formats**: PDF, DOCX, TXT
- **Technology**: RecursiveCharacterTextSplitter with 1000 character chunks and 200 character overlap
- **Output**: LangChain Document objects with metadata

### RAG System
- **Vector Store**: Chroma database for semantic search
- **Embeddings**: OpenAI embeddings for document vectorization
- **LLM**: OpenAI GPT models for response generation
- **Memory**: ConversationBufferMemory for maintaining chat history
- **Chain**: ConversationalRetrievalChain for question-answering

### User Interface
- **Framework**: Streamlit for web application
- **Features**: Document upload, chat interface, metrics display
- **Styling**: Custom CSS for professional appearance

## Data Flow

1. **Document Upload**: Users upload documents through Streamlit file uploader
2. **Text Extraction**: DocumentProcessor extracts text based on file type
3. **Chunking**: Text is split into manageable chunks with overlap
4. **Embedding**: Chunks are converted to vector embeddings using OpenAI
5. **Storage**: Embeddings stored in Chroma vector database
6. **Query Processing**: User questions are embedded and used for similarity search
7. **Context Retrieval**: Relevant document chunks retrieved from vector store
8. **Response Generation**: LLM generates responses using retrieved context
9. **Memory Update**: Conversation history is maintained for context

## External Dependencies

### Required APIs
- **OpenAI API**: For embeddings and language model capabilities
- API key required and stored in environment variables

### Python Libraries
- **streamlit**: Web application framework
- **langchain**: LLM application development framework
- **chromadb**: Vector database for embeddings
- **pypdf**: PDF text extraction
- **python-docx**: Word document processing
- **openai**: OpenAI API client
- **python-dotenv**: Environment variable management

### Storage Requirements
- Local file system for temporary document storage
- Chroma database directory for persistent vector storage

## Deployment Strategy

### Environment Setup
- Environment variables loaded from .env file
- OpenAI API key configuration required
- Python dependencies installed via requirements.txt

### Local Development
- Streamlit development server for testing
- Local Chroma database storage
- Hot reload capability for development

### Production Considerations
- Secure API key management
- Persistent storage for vector database
- Resource scaling for concurrent users
- File upload size limitations

## Changelog

- June 28, 2025. Initial setup
- June 28, 2025. Deployed files and fixed LangChain compatibility issues
- June 28, 2025. Removed API key configuration from UI for security
- June 28, 2025. Fixed ConversationalRetrievalChain model access error
- June 28, 2025. Added PostgreSQL database integration for conversation history

## User Preferences

Preferred communication style: Simple, everyday language.
