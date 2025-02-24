from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import tempfile
import os
import citationlib
import concurrent.futures

def create_citation_list(references, output_format=citationlib.Format.PLAIN):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        citations = list(executor.map(
            lambda ref: citationlib.create_citation(ref, output_format=output_format),
            references
        ))
    return citations


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
    author = "Inkwell AI"
    date = datetime.date.today().strftime("%B %d, %Y")
    font = "Source Serif 4"

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

    # Insert title with custom HEADING_1 style
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": title + "\n\n",
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": len(title) + 2},
            "paragraphStyle": {
                "namedStyleType": "HEADING_1",
                "alignment": "CENTER",
                "spaceAbove": {"magnitude": 18, "unit": "PT"},
                "spaceBelow": {"magnitude": 12, "unit": "PT"}
            },
            "fields": "namedStyleType,alignment,spaceAbove,spaceBelow"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": len(title) + 2},
            "textStyle": {
                "fontSize": {"magnitude": 24, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": {"red": 0.1, "green": 0.1, "blue": 0.1}}},
                "bold": True,
                "weightedFontFamily": {"fontFamily": font}
            },
            "fields": "fontSize,foregroundColor,bold,weightedFontFamily"
        }
    })

    # Insert author and date with custom SUBTITLE style
    metadata = f"{author}\n{date}\n\n"
    requests.append({
        "insertText": {
            "location": {"index": len(title) + 2},
            "text": metadata
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": len(title) + 2, "endIndex": len(title) + len(metadata) + 2},
            "paragraphStyle": {
                "namedStyleType": "SUBTITLE",
                "alignment": "CENTER",
                "spaceBelow": {"magnitude": 18, "unit": "PT"},
            },
            "fields": "namedStyleType,alignment,spaceBelow"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": len(title) + 2, "endIndex": len(title) + len(metadata) + 2},
            "textStyle": {
                "fontSize": {"magnitude": 12, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}},
                "italic": True,
                "weightedFontFamily": {"fontFamily": font}
            },
            "fields": "fontSize,foregroundColor,italic,weightedFontFamily"
        }
    })

    # Insert thesis with NORMAL_TEXT style
    thesis_label = "Thesis:\n"
    requests.append({
        "insertText": {
            "location": {"index": len(title) + len(metadata) + 2},
            "text": thesis_label + thesis + "\n\n"
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {
                "startIndex": len(title) + len(metadata) + 2,
                "endIndex": len(title) + len(metadata) + len(thesis_label) + len(thesis) + 4
            },
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT","alignment": "CENTER"},
            "fields": "namedStyleType,alignment"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {
                "startIndex": len(title) + len(metadata) + 2,
                "endIndex": len(title) + len(metadata) + len(thesis_label) + 2
            },
            "textStyle": {"bold": True, "weightedFontFamily": {"fontFamily": font}},
            "fields": "bold,weightedFontFamily"
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": len(title) + len(metadata) + len(thesis_label) + 2, "endIndex": len(title) + len(metadata) + len(thesis_label) + len(thesis) + 4},
            "textStyle": {"weightedFontFamily": {"fontFamily": font}},
            "fields": "weightedFontFamily"
        }
    })
    
    current_index = len(title) + len(metadata) + len(thesis_label) + len(thesis) + 4

    # Add a line break and page break after thesis
    requests.append({
        "insertText": {
            "location": {"index": current_index},
            "text": "\n"
        }
    })
    requests.append({
        "insertPageBreak": {
            "location": {"index": current_index}
        }
    })

    current_index += 1

    # Insert paragraphs with NORMAL_TEXT style
    for paragraph in paragraphs:
        start_index = current_index
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": paragraph + "\n\n"
            }
        })
        requests.append({
            "updateParagraphStyle": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": start_index + len(paragraph) + 2
                },
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"
            }
        })
        requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start_index, "endIndex": start_index + len(paragraph) + 2},
                "textStyle": {"weightedFontFamily": {"fontFamily": font}},
                "fields": "weightedFontFamily"
            }
        })
        current_index += len(paragraph) + 2

    # Add References section with HEADING_2 style
    if references and len(references) > 0:
        # Add a line break and page break before references
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": "\n"
            }
        })
        requests.append({
            "insertPageBreak": {
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
            "updateParagraphStyle": {
                "range": {
                    "startIndex": current_index,
                    "endIndex": current_index + len(references_header)
                },
                "paragraphStyle": {
                    "namedStyleType": "HEADING_2",
                    "alignment": "START",
                    "spaceAbove": {"magnitude": 24, "unit": "PT"},
                },
                "fields": "namedStyleType,alignment,spaceAbove"
            }
        })
        requests.append({
            "updateTextStyle": {
                "range": {
                    "startIndex": current_index,
                    "endIndex": current_index + len("References")
                },
                "textStyle": {
                    "fontSize": {"magnitude": 18, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": {"red": 0.2, "green": 0.2, "blue": 0.2}}},
                    "bold": True,
                    "weightedFontFamily": {"fontFamily": font}
                },
                "fields": "fontSize,foregroundColor,bold,weightedFontFamily"
            }
        })
        current_index += len(references_header)

        # Add citations with NORMAL_TEXT style
        citations = create_citation_list(references, output_format=citationlib.Format.PLAIN)
        for i, citation in enumerate(citations, 1):
            start_index = current_index
            citation += "\n\n"
            citation = citation.replace("<i>", "")
            citation = citation.replace("</i>", "")
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": citation
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": start_index + len(citation)
                    },
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType"
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": start_index + len(citation)},
                    "textStyle": {"weightedFontFamily": {"fontFamily": font}},
                    "fields": "weightedFontFamily"
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
    return f"https://docs.google.com/document/d/{doc_id}/edit"



if __name__ == "__main__":
    paragraphs = [
        "In the realm of artificial intelligence and machine learning, the development of large language models has revolutionized the way we approach natural language processing tasks. These sophisticated systems, trained on vast corpora of text data, have demonstrated remarkable capabilities in understanding and generating human-like text across a wide range of domains and applications.",
        "The architecture of these models typically involves multiple layers of neural networks, with transformer-based designs being particularly prominent in recent years. These architectures employ self-attention mechanisms that allow the model to weigh the importance of different words in a sentence, enabling more nuanced understanding and generation of contextually relevant text.",
        "One of the most significant challenges in developing these models is the computational resources required for training. The process often necessitates the use of specialized hardware such as GPUs or TPUs, along with distributed computing frameworks to handle the massive scale of data and parameters involved in the training process.",
        "Despite these challenges, the potential applications of large language models are vast and varied. They are being used in fields ranging from content creation and customer service to scientific research and education, demonstrating their versatility and impact across multiple sectors of society.",
        "As we continue to develop and refine these models, it is crucial to consider the ethical implications of their use. Issues such as bias in training data, potential misuse of generated content, and the impact on employment in certain industries must be carefully addressed to ensure that the benefits of this technology are distributed equitably and responsibly."
    ]
    thesis = "This is a test thesis."
    title = "Test Document"
    references = [
        "https://doi.org/10.1080/00461520.2012.722805",
        "https://arxiv.org/abs/2401.03428",
        "https://www.nytimes.com/2025/02/08/us/politics/treasury-systems-raised-security-concerns.html"
    ]
    create_document(paragraphs=paragraphs, thesis=thesis, title=title, references=references)
