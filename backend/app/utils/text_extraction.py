import pypdf
import docx

def extract_text_from_file(file_path: str, mime_type: str) -> list[dict]:
    pages = []
    
    if mime_type == "application/pdf":
        reader = pypdf.PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page_number": i + 1,
                    "text": text
                })
                
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file_path)
        paragraphs_text = [p.text for p in doc.paragraphs]
        full_text = "\n".join(paragraphs_text)
        
        if full_text and full_text.strip():
            pages.append({
                "page_number": 1,
                "text": full_text
            })
            
    else:
        raise ValueError("Unsupported file type: " + mime_type)
        
    return pages
