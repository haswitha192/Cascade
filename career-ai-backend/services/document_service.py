import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


def get_client():
    endpoint = os.getenv("DOC_INT_ENDPOINT")
    key = os.getenv("DOC_INT_KEY")

    if not endpoint or not key:
        raise ValueError("Document Intelligence credentials not configured.")

    return DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )


def analyze_resume(file_bytes: bytes):

    client = get_client()

    poller = client.begin_analyze_document(
        "prebuilt-layout",
        file_bytes
    )

    result = poller.result()

    extracted_text = ""

    for page in result.pages:
        for line in page.lines:
            extracted_text += line.content + "\n"

    ai_feedback = "Resume evaluation temporarily disabled"

    return {
        "extracted_text": extracted_text,
        "ai_feedback": ai_feedback
    }