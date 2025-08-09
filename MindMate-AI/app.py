import streamlit as st
import os
from file_parser import extract_text_from_pdf
from chatbot import answer_query
from youtube_parser import extract_video_id, get_transcript, summarize_transcript

st.set_page_config(page_title="🧠 MindMate AI", layout="wide")
st.title("🧠 MindMate AI")
st.subheader("Chat with any PDF file using Groq-powered LLM")

tab1, tab2 = st.tabs(["📄 PDF Q&A", "📺 YouTube Summarizer"])


with tab1:
    st.subheader("📄 Upload a PDF and ask questions")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])


    if uploaded_file:
        with st.spinner("Reading your file..."):
            file_path = os.path.join("assets", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            file_text = extract_text_from_pdf(file_path)

        st.success("File loaded! Ask any question below.")
        user_question = st.text_input("Ask something about the file content:")

        if user_question:
            with st.spinner("Thinking..."):
                answer = answer_query(file_text, user_question)
                st.write("**Answer:**")
                st.success(answer)


with tab2:
    st.subheader("📺 YouTube Video Summarizer")
    st.markdown("Paste a YouTube link to generate detailed notes and a summary of the video content.")
    
    # Add some styling
    st.markdown("""
    <style>
    .youtube-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .transcript-box {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 1rem;
        max-height: 300px;
        overflow-y: auto;
        margin: 1rem 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)
    
    yt_link = st.text_input("Enter YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
    
    # Initialize session state for YouTube tab
    if 'show_transcript' not in st.session_state:
        st.session_state.show_transcript = False
    if 'transcript_text' not in st.session_state:
        st.session_state.transcript_text = ""
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    
    if yt_link:
        with st.spinner("🔍 Extracting video ID..."):
            video_id = extract_video_id(yt_link)
            
            if not video_id:
                st.error("❌ Invalid YouTube URL. Please check the link and try again.")
                st.stop()
                
            st.success(f"✅ Found video ID: {video_id}")
            
            # Display video thumbnail and title
            try:
                from pytube import YouTube
                yt = YouTube(f"https://youtube.com/watch?v={video_id}")
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(yt.thumbnail_url, width=200)
                with col2:
                    st.subheader(yt.title)
                    st.caption(f"By: {yt.author}")
            except Exception as e:
                st.warning(f"Couldn't fetch video details: {str(e)}")
            
            with st.spinner("📝 Extracting transcript..."):
                transcript_text, success = get_transcript(video_id)
                
                if not success:
                    st.error(f"❌ {transcript_text}")
                    st.info("💡 Try a different video or check if captions are available.")
                    st.stop()
                
                st.session_state.transcript_text = transcript_text
                st.success(f"✅ Successfully extracted transcript ({len(transcript_text):,} characters)")
        
        # Show transcript toggle
        if st.button("👁️ Toggle Transcript"):
            st.session_state.show_transcript = not st.session_state.show_transcript
            
        if st.session_state.show_transcript and st.session_state.transcript_text:
            st.markdown("### 📜 Full Transcript")
            st.markdown(f'<div class="transcript-box">{st.session_state.transcript_text}</div>', 
                       unsafe_allow_html=True)
        
        # Summary section
        st.markdown("---")
        st.subheader("📝 Video Summary")
        
        if st.button("✨ Generate Summary", type="primary"):
            with st.spinner("🧠 Analyzing content and generating summary..."):
                try:
                    summary = summarize_transcript(st.session_state.transcript_text)
                    st.session_state.summary = summary
                    
                    # Display the summary
                    st.markdown("### 🎯 Key Points")
                    st.markdown(summary)
                    
                    # Add download button for the summary
                    st.download_button(
                        label="💾 Download Summary",
                        data=summary,
                        file_name=f"youtube_summary_{video_id}.md",
                        mime="text/markdown"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error generating summary: {str(e)}")
                    st.error("Please try again or try a different video.")
        
        # Display existing summary if available
        elif st.session_state.summary:
            st.markdown("### 🎯 Key Points")
            st.markdown(st.session_state.summary)
            
            # Add download button for the summary
            st.download_button(
                label="💾 Download Summary",
                data=st.session_state.summary,
                file_name=f"youtube_summary_{video_id}.md",
                mime="text/markdown"
            )
    else:
        st.info("👆 Please enter a YouTube video URL above to get started.")