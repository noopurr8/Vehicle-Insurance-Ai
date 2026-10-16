import easyocr
import re

# Load OCR model once
reader = easyocr.Reader(["en"], gpu=False)


def extract_text(image_path):
    results = reader.readtext(image_path)

    text_lines = [result[1] for result in results]

    return "\n".join(text_lines)


def extract_fields(text):
    fields = {
        "vehicle_number": None,
        "policy_number": None,
        "name": None,
        "expiry_date": None,
    }

    # Indian vehicle registration number
    vehicle_pattern = r"\b[A-Z]{2}[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{4}\b"
    vehicle_match = re.search(vehicle_pattern, text.upper())

    if vehicle_match:
        fields["vehicle_number"] = vehicle_match.group().replace(" ", "-")

    # Policy number
    policy_match = re.search(
        r"(?:policy\s*(?:no|number|#)?\s*[:\-]?\s*)([A-Z0-9\/\-]+)",
        text,
        re.IGNORECASE
    )

    if policy_match:
        fields["policy_number"] = policy_match.group(1)

    # Expiry date
    date_match = re.search(
        r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
        text
    )

    if date_match:
        fields["expiry_date"] = date_match.group()

    return fields


def process_document(image_path):
    text = extract_text(image_path)
    fields = extract_fields(text)

    return {
        "raw_text": text,
        "extracted_fields": fields
    }


if __name__ == "__main__":
    print("OCR service ready.")