import re

def chunk_pages(pages: list[dict], chunk_size_tokens: int = 600, overlap_tokens: int = 100) -> list[dict]:
    """
    Chunks text from multiple pages into smaller pieces based on paragraph boundaries.
    
    Note: This uses a simple whitespace-based word-count approximation for "tokens" 
    (splitting on whitespace). This is an approximation, not a real tokenizer, 
    but is sufficient for prototype chunk-sizing purposes.
    """
    chunks = []
    chunk_index = 0
    
    current_items = []
    current_word_count = 0
    
    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text", "")
        
        # Normalize newlines: convert \r\n to \n, then multiple \n to a single \n
        # This handles splitting on \n\n or \n, whichever the text uses.
        normalized_text = re.sub(r'\n+', '\n', text.replace('\r\n', '\n'))
        paragraphs = [p.strip() for p in normalized_text.split('\n') if p.strip()]
        
        for para in paragraphs:
            para_words = para.split()
            para_word_count = len(para_words)
            
            if not para_word_count:
                continue
                
            # If adding this paragraph exceeds the chunk size and we already have content
            if current_word_count + para_word_count > chunk_size_tokens and current_items:
                # 1. Finalize current chunk
                chunk_text = "\n\n".join(item["text"] for item in current_items)
                
                # Determine majority page
                page_word_counts = {}
                for item in current_items:
                    pn = item["page_number"]
                    page_word_counts[pn] = page_word_counts.get(pn, 0) + item["word_count"]
                
                majority_page = max(page_word_counts.keys(), key=lambda k: page_word_counts[k])
                
                chunk_words = chunk_text.split()
                actual_token_count = len(chunk_words)
                
                if chunk_text.strip():
                    chunks.append({
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "page_number": majority_page,
                        "token_count": actual_token_count
                    })
                    chunk_index += 1
                
                # 2. Start next chunk with overlap
                if overlap_tokens > 0:
                    overlap_words = chunk_words[-overlap_tokens:]
                    overlap_text = " ".join(overlap_words)
                    
                    last_page = current_items[-1]["page_number"]
                    
                    current_items = [{
                        "text": overlap_text,
                        "page_number": last_page,
                        "word_count": len(overlap_words)
                    }]
                    current_word_count = len(overlap_words)
                else:
                    current_items = []
                    current_word_count = 0

            # Add the current paragraph to the buffer
            current_items.append({
                "text": para,
                "page_number": page_num,
                "word_count": para_word_count
            })
            current_word_count += para_word_count
            
    # Finalize any remaining items in the buffer
    if current_items:
        chunk_text = "\n\n".join(item["text"] for item in current_items)
        if chunk_text.strip():
            chunk_words = chunk_text.split()
            
            page_word_counts = {}
            for item in current_items:
                pn = item["page_number"]
                page_word_counts[pn] = page_word_counts.get(pn, 0) + item["word_count"]
            
            majority_page = max(page_word_counts.keys(), key=lambda k: page_word_counts[k])
            
            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text,
                "page_number": majority_page,
                "token_count": len(chunk_words)
            })

    return chunks
