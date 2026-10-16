from ai.ocr.ocr_service import process_document


def process_claim_document(image_path):
    """
    Process an insurance document using OCR.
    """

    result = process_document(image_path)

    return {
        "ocr_text": result["raw_text"],
        "extracted_fields": result["extracted_fields"]
    }