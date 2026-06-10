def is_pdf(file_content: bytes, content_type: str) -> bool:
    # Verify content type
    if content_type != "application/pdf":
        return False
    # Verify magic bytes: PDF files start with %PDF- (hex: 25 50 44 46 2d)
    if not file_content.startswith(b"%PDF-"):
        return False
    return True
