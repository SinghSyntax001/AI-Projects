from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import Tuple, Optional
import logging
import re
from llm_config import get_groq_completion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_transcript(video_id: str) -> Tuple[str, bool]:
    """
    Fetch transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID (11 characters)
        
    Returns:
        Tuple of (transcript_text, success_status)
    """
    if not video_id or len(video_id) != 11:
        error_msg = f"Invalid video ID: {video_id}. Must be exactly 11 characters."
        logger.error(error_msg)
        return error_msg, False
        
    try:
        logger.info(f"Attempting to fetch transcript for video ID: {video_id}")
        
        # First try getting the default transcript (usually English)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info(f"Successfully retrieved default transcript for video {video_id}")
        except NoTranscriptFound:
            # If no default transcript, try to list available languages
            logger.info(f"No default transcript found for {video_id}. Checking available languages...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript if available
            try:
                transcript = transcript_list.find_transcript(['en']).fetch()
                logger.info(f"Found English transcript for video {video_id}")
            except Exception as e:
                # If no English, try any available transcript
                try:
                    transcript = next(iter(transcript_list)).fetch()
                    logger.info(f"Found transcript in another language for video {video_id}")
                except Exception as inner_e:
                    logger.error(f"No transcript available in any language: {str(inner_e)}")
                    return "No transcript available for this video in any language.", False
        
        # Process the transcript
        full_text = " ".join([item["text"].strip() for item in transcript if item.get("text")])
        
        if not full_text.strip():
            error_msg = "Transcript is empty or contains no text."
            logger.error(error_msg)
            return error_msg, False
            
        logger.info(f"Successfully processed transcript for video {video_id} (length: {len(full_text)} chars)")
        return full_text, True
        
    except TranscriptsDisabled:
        error_msg = "Subtitles are disabled for this video."
        logger.error(error_msg)
        return error_msg, False
    except NoTranscriptFound:
        error_msg = "No transcript available for this video."
        logger.error(error_msg)
        return error_msg, False
    except Exception as e:
        error_msg = f"Failed to fetch transcript: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg, False

def extract_video_id(yt_url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Supports:
    - Regular URLs: https://www.youtube.com/watch?v=VIDEO_ID
    - Short URLs: https://youtu.be/VIDEO_ID
    - Embed URLs: https://www.youtube.com/embed/VIDEO_ID
    - With timestamps: https://youtu.be/VIDEO_ID?t=123
    - With other parameters: https://www.youtube.com/watch?v=VIDEO_ID&feature=share
    - Just the video ID
    """
    if not yt_url or not isinstance(yt_url, str):
        return None
        
    yt_url = yt_url.strip()
    
    # List of regex patterns to match YouTube video IDs in different URL formats
    patterns = [
        # Standard YouTube watch URL
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/watch/\?v=)([^&\n?#]*)',
        # Alternative patterns that might appear in various YouTube URLs
        r'(?:v=|v/|/videos/|embed\/|youtu\.be\/|\/v\/|watch\?v=|\&v=)([^\&\?\n ]*)',
        # Just the video ID (11 character string)
        r'^([a-zA-Z0-9_-]{11})$',
        # YouTube Shorts
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, yt_url, re.IGNORECASE)
        if match:
            # Get the first group that matched (the video ID)
            video_id = match.group(1)
            # Clean up any trailing characters that might be part of the URL
            video_id = video_id.split('?')[0].split('&')[0].split('#')[0]
            # YouTube video IDs are always 11 characters
            if len(video_id) == 11:
                return video_id
    
    # If we get here, no valid video ID was found
    logger.warning(f"Could not extract video ID from URL: {yt_url}")
    return None
    
def chunk_text(text: str, max_chunk_size: int = 4000) -> list[str]:
    """Split text into chunks of specified size, trying to break at sentence boundaries."""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    while text:
        # Find the last period within the chunk size
        chunk = text[:max_chunk_size]
        last_period = chunk.rfind('.')
        
        if last_period > max_chunk_size * 0.8:  # Only break if we find a good sentence boundary
            chunk = chunk[:last_period + 1]
            text = text[last_period + 1:].lstrip()
        else:
            # If no good sentence boundary, just split at max_chunk_size
            text = text[max_chunk_size:]
        
        chunks.append(chunk)
    
    return chunks

def summarize_transcript(transcript_text: str, chunk_size: int = 4000) -> str:
    """
    Summarize a YouTube transcript, handling long transcripts by chunking.
    
    Args:
        transcript_text: Full transcript text
        chunk_size: Maximum size for each chunk of text to process
        
    Returns:
        str: Formatted summary of the transcript
    """
    # Clean and preprocess the transcript
    transcript_text = ' '.join(transcript_text.split())  # Normalize whitespace
    
    # Split into chunks if needed
    chunks = chunk_text(transcript_text, chunk_size)
    
    if len(chunks) == 1:
        # If transcript is short, process in one go
        return _summarize_chunk(chunks[0])
    else:
        # For long transcripts, summarize each chunk and then combine
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            summary = _summarize_chunk(chunk, chunk_num=i, total_chunks=len(chunks))
            chunk_summaries.append(summary)
        
        # Combine chunk summaries into a final summary
        combined_summary = '\n\n'.join(chunk_summaries)
        return _summarize_chunk(combined_summary, is_final=True)

def _summarize_chunk(chunk: str, chunk_num: int = 1, total_chunks: int = 1, is_final: bool = False) -> str:
    """Helper function to summarize a single chunk of text."""
    if is_final:
        prompt = f"""
You are a helpful assistant that creates comprehensive summaries from multiple text chunks.
Please combine the following chunk summaries into one cohesive, well-structured summary.
Focus on maintaining the key points and logical flow.

Chunk summaries:
{chunk}

Please provide a final summary that includes:
1. Main topics covered
2. Key points for each topic
3. Any important conclusions or takeaways

Format the summary with clear section headers and bullet points for readability.
"""
    else:
        chunk_info = f"(Chunk {chunk_num} of {total_chunks})" if total_chunks > 1 else ""
        prompt = f"""
You are a helpful assistant that summarizes educational YouTube transcripts into clear, 
concise bullet points. This is {chunk_info} of the full transcript.

Transcript portion:
{chunk}

Please summarize the key points in 5-10 bullet points. For each point:
- Start with a clear, concise statement
- Include important details and examples
- Use markdown formatting for better readability
- Focus on educational content and key takeaways

If this is a technical topic, include relevant technical details.
"""
    
    try:
        summary = get_groq_completion(prompt)
        return summary.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        if is_final:
            return "Error: Failed to generate final summary. Please try again."
        return "[Summary unavailable for this section]"

