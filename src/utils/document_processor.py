from typing import Union
import mimetypes

# Supported code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.cpp', '.c', '.h', '.hpp',
    '.java', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt',
    '.m', '.mm', '.scala', '.sh', '.bash', '.zsh', '.ps1',
    '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.sql', '.r', '.R', '.lua', '.perl', '.pl'
}

# Supported text file extensions
TEXT_EXTENSIONS = {'.txt', '.md', '.markdown', '.rst', '.log'}

def is_text_file(filename: str, file_type: str) -> bool:
    """Determine if a file should be treated as text."""
    # Check MIME type
    if file_type in ['text/plain', 'text/markdown', 'text/x-python', 
                     'text/x-c', 'text/x-c++', 'text/javascript',
                     'application/javascript', 'application/json',
                     'application/xml', 'text/html', 'text/css']:
        return True
    
    # Check file extension
    import os
    _, ext = os.path.splitext(filename.lower())
    return ext in CODE_EXTENSIONS or ext in TEXT_EXTENSIONS


def extract_text(content: bytes, file_type: str, filename: str = "") -> str:
    """Extract text from various file formats.
    
    Args:
        content: Raw file bytes
        file_type: MIME type of the file
        filename: Original filename (used for extension detection)
    
    Returns:
        Extracted text content
    """
    # Handle text-based files (plain text, markdown, code)
    if file_type in ["text/plain", "text/markdown"] or is_text_file(filename, file_type):
        # Try UTF-8 first, fall back to latin-1 if that fails
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1")
            except Exception:
                return content.decode("utf-8", errors="replace")
    
    elif file_type == "application/pdf":
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        try:
            import docx
            from io import BytesIO
            
            doc_file = BytesIO(content)
            doc = docx.Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    else:
        # Last resort: try to decode as text
        if is_text_file(filename, file_type):
            try:
                return content.decode("utf-8", errors="replace")
            except Exception as e:
                raise ValueError(f"Failed to decode text file: {str(e)}")
        else:
            raise ValueError(f"Unsupported file type: {file_type}. Use /download endpoint for binary files.")
