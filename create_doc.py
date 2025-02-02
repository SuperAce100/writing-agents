from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

def create_document(paragraphs, thesis, title, references=None):
    # Replace with your service account file and scope
    SERVICE_ACCOUNT_FILE = "./keys/writing-agents-2b3410302d32.json"
    SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Sample data (replace with your own references)
    author = "Written by AI"
    date = datetime.date.today().strftime("%B %d, %Y")

    # Utility function to create styled insertText requests
    def create_insert_request(index, text, bold=False, heading=None):
        request = {
            "insertText": {
                "location": {"index": index},
                "text": text
            }
        }
        if bold or heading:
            request["insertTextStyle"] = {
                "style": {
                    "bold": bold,
                    "headingId": heading
                }
            }
        return request

    # 1. Create a new Google Doc
    new_doc = {"title": title}
    created_doc = docs_service.documents().create(body=new_doc).execute()
    doc_id = created_doc.get("documentId")
    print(f"Created doc with ID: {doc_id}")

    # 2. Build batchUpdate requests to insert content
    requests = []

    # Insert title as a header
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": title + "\n\n"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": len(title) + 2},
            "textStyle": {"bold": True, "fontSize": {"magnitude": 18, "unit": "PT"}},
            "fields": "bold,fontSize"
        }
    })

    # Insert author and date
    metadata = f"Author: {author}\nDate: {date}\n\n"
    requests.append({
        "insertText": {
            "location": {"index": len(title) + 2},
            "text": metadata
        }
    })

    # Insert thesis
    thesis_label = "Thesis:\n"
    requests.append({
        "insertText": {
            "location": {"index": len(title) + len(metadata) + 2},
            "text": thesis_label + thesis + "\n\n"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {
                "startIndex": len(title) + len(metadata) + 2,
                "endIndex": len(title) + len(metadata) + len(thesis_label) + 2
            },
            "textStyle": {"bold": True},
            "fields": "bold"
        }
    })

    current_index = len(title) + len(metadata) + len(thesis_label) + len(thesis) + 4


    requests.append({
        "insertHorizontalRule": {
            "location": {"index": current_index}
        }
    })

    current_index += 1


    # Insert each paragraph
    for paragraph in paragraphs:
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": paragraph + "\n\n"
            }
        })
        current_index += len(paragraph) + 2

    # Add References section if references are provided
    if references and len(references) > 0:
        # Add a horizontal rule before references
        requests.append({
            "insertHorizontalRule": {
                "location": {"index": current_index}
            }
        })
        current_index += 1

        # Add References header
        references_header = "References\n\n"
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": references_header
            }
        })
        requests.append({
            "updateTextStyle": {
                "range": {
                    "startIndex": current_index,
                    "endIndex": current_index + len("References")
                },
                "textStyle": {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"}},
                "fields": "bold,fontSize"
            }
        })
        current_index += len(references_header)

        # Add each reference
        for i, ref in enumerate(references, 1):
            citation = f"[{i}] {ref}\n"
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": citation
                }
            })
            current_index += len(citation)

    # 3. Send the update requests
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests}
    ).execute()

    # 4. Set document permissions
    permission = {
        "type": "anyone",  # Public access
        "role": "reader"   # Read-only (use 'writer' for edit access)
    }
    drive_service.permissions().create(
        fileId=doc_id,
        body=permission
    ).execute()

    print(f"Document created successfully! View it at: https://docs.google.com/document/d/{doc_id}/edit")
