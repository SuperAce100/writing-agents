from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import tempfile
import os
from markdown_pdf import MarkdownPdf, Section
from citations import create_citation_list

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
    return f"https://docs.google.com/document/d/{doc_id}/edit"

def create_doc_markdown(paragraphs, thesis, title, references=None):
    """
    Creates a professional PDF document from markdown content with proper formatting.
    
    Args:
        paragraphs (list): List of paragraph strings for main content
        thesis (str): Thesis statement
        title (str): Document title
        references (list, optional): List of reference strings
        
    Returns:
        str: Path to generated PDF file
    """
    # Initialize PDF without TOC
    pdf = MarkdownPdf(toc_level=0)
    
    # Create title page with centered content and proper spacing
    title_content = (
        "<div style='text-align: center; margin-top: 4in;'>\n\n"
        f"# {title}\n\n"
        "<br/><br/>\n\n"
        "Written by AI\n\n"
        f"{datetime.datetime.now().strftime('%B %d, %Y')}\n\n"
        "<br/><br/><br/>\n\n"
        "**Thesis Statement**\n\n"
        f"*{thesis}*\n\n"
        "</div>\n\n"
        "<div style='page-break-after: always;'></div>\n\n"
    )
    title_section = Section(title_content, toc=False)
    pdf.add_section(title_section)

    content = ""

    # Create main content section with proper paragraph formatting
    for paragraph in paragraphs:
        # Add paragraph with proper spacing and indentation
        content += f"<div style='text-align: justify; text-indent: 2em;'>\n{paragraph}</div>\n\n"
    
    content_section = Section(content)
    pdf.add_section(content_section)

    # Add references section if provided with proper formatting
    if references:
        citations = create_citation_list(references)
        ref_content = "<div>\n\n"
        ref_content += "# Bibliography\n\n"
        # Sort citations alphabetically by first author's last name
        citations.sort(key=lambda x: x.split(',')[0].strip() if ',' in x else x)
        for citation in citations:
            # Format each reference with hanging indent and double spacing
            ref_content += (
                f"<div style='padding-left: 2em; text-indent: -2em; margin-bottom: 1em;'>\n"
                f"{citation}\n"
                "</div>\n\n"
            )
        ref_content += "</div>"
        ref_section = Section(ref_content)
        pdf.add_section(ref_section)

    print("here")
    # Set PDF metadata with additional fields
    pdf.meta.update({
        "title": title,
        "author": "Written by AI",
        "creationDate": str(datetime.datetime.now()),
        "keywords": "academic paper, thesis",
        "subject": thesis
    })


    # Create output directory and save PDF
    pdf_path = "./outputs/output.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    try:
        pdf.save(pdf_path)
        print(f"PDF successfully created at: {pdf_path}")
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        return None

    return pdf_path


if __name__ == "__main__":
    paragraphs = ["This is a test paragraph.", "This is another test paragraph."]
    thesis = "This is a test thesis."
    title = "Test Document"
    references = [
        "https://doi.org/10.1080/00461520.2012.722805",
        "https://arxiv.org/abs/2401.03428",
        "https://www.nytimes.com/2025/02/08/us/politics/treasury-systems-raised-security-concerns.html"
    ]
    # create_document(paragraphs=paragraphs, thesis=thesis, title=title, references=citations)
    create_doc_markdown(paragraphs=paragraphs, thesis=thesis, title=title, references=references)
