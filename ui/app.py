import streamlit as st
import sys
import os
import time
from pypdf import PdfReader # Import pypdf

# Add the parent directory to sys.path to allow imports from src and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import OllamaAgent
from utils.hardware import get_system_info, recommend_model

st.set_page_config(page_title="Ollama AI Agent", layout="wide")

def main():
    st.title("🤖 Local AI Agent with Ollama")

    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "llama3.2"

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Hardware Info
        with st.expander("Hardware Check", expanded=True):
            sys_info = get_system_info()
            st.write(f"**RAM:** {sys_info['available_ram_gb']}GB available / {sys_info['total_ram_gb']}GB total")
            if sys_info['gpu_available']:
                st.write(f"**GPU:** {sys_info['gpu_name']} ({sys_info['vram_gb']}GB VRAM)")
            else:
                st.write("**GPU:** Not detected (or no NVIDIA driver)")
            
            rec = recommend_model(sys_info)
            st.info(f"💡 Recommendation: **{rec['recommended_model']}**")
            st.caption(rec['reason'])

        # Model Management
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        agent = OllamaAgent(host=ollama_host)
        
        try:
            models_info = agent.list_models()
            model_names = [m['model'] for m in models_info]
        except Exception:
            st.error("Could not connect to Ollama. Make sure it is running!")
            model_names = []

        # If recommended model is not in list (and list is not empty), maybe warn?
        # But we just let user select.
        
        selected_model = st.selectbox(
            "Select Model", 
            model_names, 
            index=model_names.index(st.session_state.selected_model) if st.session_state.selected_model in model_names else 0
        )
        st.session_state.selected_model = selected_model
        
        # Update agent model
        agent.model_name = selected_model

        st.divider()
        
        # Pull new model
        new_model_name = st.text_input("Pull new model (e.g. llama3.2)")
        if st.button("Download Model"):
            if new_model_name:
                status_text = st.empty()
                progress_bar = st.progress(0)
                try:
                    for progress in agent.pull_model(new_model_name):
                        if 'completed' in progress and 'total' in progress:
                            p = progress['completed'] / progress['total']
                            progress_bar.progress(p)
                            status_text.text(f"Downloading: {int(p*100)}% - {progress.get('status', '')}")
                        else:
                            status_text.text(progress.get('status', ''))
                    st.success(f"Model {new_model_name} pulled successfully!")
                    time.sleep(1) # wait a bit
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to pull model: {str(e)}")

    # --- Main Chat ---
    
    # Context Uploads
    with st.expander("📂 Add Context (Images/Files)", expanded=False):
        uploaded_images = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        uploaded_files = st.file_uploader("Upload Text/PDF Files", type=['txt', 'md', 'py', 'json', 'pdf'], accept_multiple_files=True)

    # Process uploads
    current_images = []
    if uploaded_images:
        for img_file in uploaded_images:
            current_images.append(agent.process_image(img_file))
            st.image(img_file, caption=img_file.name, width=200)

    file_context = ""
    if uploaded_files:
        for text_file in uploaded_files:
            try:
                # Handle PDF files
                if text_file.name.lower().endswith('.pdf'):
                    pdf_reader = PdfReader(text_file)
                    content = ""
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
                else:
                    # Handle text-based files
                    content = text_file.read().decode('utf-8')
                
                file_context += f"\n--- Content of {text_file.name} ---\n{content}\n"
            except Exception as e:
                st.error(f"Error reading {text_file.name}: {e}")
        if file_context:
            st.success(f"Added {len(uploaded_files)} files to context.")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If we were storing images in history, we'd display them here too, 
            # but usually we just send them to the model for the current turn or keep them in backend state.
            # Simplified for now: text history display.

    # User Input
    if prompt := st.chat_input("Ask something..."):
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepare full context if files were uploaded
        final_prompt = prompt
        if file_context:
            final_prompt = f"Context from files:\n{file_context}\n\nUser Question: {prompt}"

        # Add to history (UI state)
        # Note: We don't save the full file content in the UI history to keep it clean, 
        # or we could save it as "attached files".
        # For the AGENT, we pass the full history plus current prompt.
        
        # Basic state update
        st.session_state.messages.append({"role": "user", "content": prompt}) # Saving pure prompt for display
        
        # If we have file context, we might want to inject it into the message sent to Ollama 
        # but pretend to the user it's just the prompt, or show it. 
        # Let's constructing the actual messages payload for Ollama.
        
        ollama_messages = [
            {"role": m["role"], "content": m["content"]} 
            for m in st.session_state.messages[:-1] # All previous
        ]
        
        # Current message with context
        current_msg_payload = {
            "role": "user", 
            "content": final_prompt
        }
        if current_images:
            current_msg_payload["images"] = current_images
            
        ollama_messages.append(current_msg_payload)

        # Describe what is happening
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""
            
            # Streaming response
            for chunk in agent.chat(messages=ollama_messages, stream=True):
                if 'message' in chunk:
                    content = chunk['message'].get('content', '')
                    full_response += content
                    response_container.markdown(full_response + "▌")
                if 'error' in chunk:
                    st.error(chunk['error'])
            
            response_container.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
