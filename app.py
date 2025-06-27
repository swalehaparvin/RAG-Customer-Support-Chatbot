import streamlit as st
import os
from dotenv import load_dotenv
import tempfile
from pathlib import Path

# Load environment variables
load_dotenv()

# Import our RAG system
from rag_system import CustomerSupportRAG
from document_processor import DocumentProcessor

# Page config
st.set_page_config(
    page_title="🤖 AI Customer Support",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False

def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🤖 AI-Powered Customer Support</h1>
            <p>Upload documents, ask questions, get instant answers with source citations</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # OpenAI API Key input
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Enter your OpenAI API key"
        )
        
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        
        st.divider()
        
        # Document upload section
        st.header("📄 Knowledge Base")
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'txt', 'docx'],
            accept_multiple_files=True,
            help="Upload PDF, TXT, or DOCX files to build your knowledge base"
        )
        
        if uploaded_files and openai_key:
            if st.button("🔄 Process Documents", type="primary"):
                process_documents(uploaded_files)
        
        # Display document status
        if st.session_state.documents_loaded:
            st.success("✅ Documents processed successfully!")
            
            # Show document stats
            if st.session_state.rag_system:
                stats = st.session_state.rag_system.get_stats()
                st.metric("Documents", stats['doc_count'])
                st.metric("Text Chunks", stats['chunk_count'])
        
        st.divider()
        
        # Model settings
        st.header("🔧 Model Settings")
        model = st.selectbox(
            "Choose Model",
            ["gpt-3.5-turbo", "gpt-4"],
            index=0,
            help="GPT-4 is more accurate but slower and more expensive"
        )
        
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.1,
            help="Lower values = more focused answers"
        )
        
        # Save settings to session state
        st.session_state.model = model
        st.session_state.temperature = temperature

    # Main chat interface
    if not openai_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started.")
        st.info("""
        **To get started:**
        1. Get an OpenAI API key from https://platform.openai.com/api-keys
        2. Enter it in the sidebar
        3. Upload some documents
        4. Start asking questions!
        """)
        return
    
    if not st.session_state.documents_loaded:
        st.info("📄 Upload some documents in the sidebar to build your knowledge base first!")
        
        # Show sample questions
        st.subheader("💡 Example Use Cases")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Banking Support:**
            - "How do I reset my online banking password?"
            - "What are the fees for international transfers?"
            - "How to apply for a credit card?"
            """)
        
        with col2:
            st.markdown("""
            **Insurance Support:**
            - "What does my policy cover?"
            - "How to file a claim?"
            - "What are my deductible amounts?"
            """)
        return
    
    # Chat interface
    st.subheader("💬 Ask Questions About Your Documents")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, (question, answer, sources) in enumerate(st.session_state.chat_history):
            # User message
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {question}
                </div>
            """, unsafe_allow_html=True)
            
            # Bot response
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>AI Assistant:</strong> {answer}
                </div>
            """, unsafe_allow_html=True)
            
            # Sources
            if sources:
                with st.expander(f"📚 Sources for answer {i+1}"):
                    for j, source in enumerate(sources):
                        st.write(f"**Source {j+1}:** {source}")
    
    # Question input
    question = st.text_input(
        "Ask a question:",
        placeholder="e.g., What are the account opening requirements?",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        ask_button = st.button("🚀 Ask", type="primary")
    
    if (ask_button or question) and question:
        answer_question(question)
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

def process_documents(uploaded_files):
    """Process uploaded documents and build vector store"""
    
    with st.spinner("🔄 Processing documents... This may take a few minutes."):
        try:
            # Initialize document processor
            processor = DocumentProcessor()
            
            # Process each uploaded file
            all_documents = []
            progress_bar = st.progress(0)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Process document
                documents = processor.process_file(tmp_file_path, uploaded_file.name)
                all_documents.extend(documents)
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            # Initialize RAG system with processed documents
            st.session_state.rag_system = CustomerSupportRAG()
            st.session_state.rag_system.build_vector_store(all_documents)
            st.session_state.documents_loaded = True
            
            st.success(f"✅ Successfully processed {len(uploaded_files)} documents!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing documents: {str(e)}")

def answer_question(question):
    """Get answer from RAG system"""
    
    if not st.session_state.rag_system:
        st.error("❌ Please process documents first!")
        return
    
    with st.spinner("🤔 Thinking..."):
        try:
            # Get answer from RAG system
            result = st.session_state.rag_system.ask_question(
                question,
                model=st.session_state.get('model', 'gpt-3.5-turbo'),
                temperature=st.session_state.get('temperature', 0.1)
            )
            
            # Add to chat history
            st.session_state.chat_history.append((
                question,
                result['answer'],
                result['sources']
            ))
            
            # Clear input and refresh
            st.session_state.question_input = ""
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error getting answer: {str(e)}")

if __name__ == "__main__":
    main()