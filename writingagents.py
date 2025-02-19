import os
import time
from openai import OpenAI
from pydantic import BaseModel
from enum import Enum
from typing import List, Dict, Optional, Callable
import pprint
import create_doc
import streamlit as st
import concurrent.futures
from typing import Tuple, Any

# Set page config
st.set_page_config(
    page_title="QuillAI",
    page_icon="🪶",
)

class ParagraphType(str, Enum):
    introduction = "introduction"
    expository = "expository"
    argumentative = "argumentative"
    comparative = "comparative"
    synthesizing = "synthesizing"
    counterargument = "counterargument"
    transitional = "transitional"
    analytical = "analytical"
    evaluative = "evaluative"
    conclusion = "conclusion"

class Paragraph(BaseModel):
    number: int
    name: str
    paragraphType: ParagraphType
    prompt: str

class PaperStructure(BaseModel):
    title: str
    thesis: str
    paragraphs: List[Paragraph]

class ResearchPlan(BaseModel):
    searches: List[str]

class WritingAgent:
    def __init__(self, model: str = "gpt-4o-mini-2024-07-18"):
        self.client = OpenAI()
        self.perplexity = OpenAI(
            api_key=os.environ["PERPLEXITY_API_KEY"], 
            base_url="https://api.perplexity.ai"
        )
        self.model = model
        self.search_model = "sonar"

    def generate_research_plan(self, topic: str) -> ResearchPlan:
        """Generate a research plan with search queries based on the topic."""
        research_planner_system_prompt = """
        You are a research assistant that helps with the planning of a research paper. Given a topic, you will provide a list of 3-5 searches that will provide helpful information for the paper.
        """

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": research_planner_system_prompt},
                {"role": "user", "content": topic}
            ],
            response_format=ResearchPlan, 
        )
        return response.choices[0].message.parsed

    def _execute_single_search(self, search: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Execute a single search query and return the response and citations."""
        research_system_prompt = """
        You are a highly capable research assistant specializing in academic research and providing scholarly, authoritative, and credible sources. Your primary goal is to assist someone writing an argumentative paper by identifying and summarizing the most relevant and reliable sources available on the internet. 

        Focus on delivering:
        1. **Scholarly Articles**: Peer-reviewed journal articles, conference papers, and research studies from reputable academic publishers (e.g., Springer, IEEE, Elsevier, JSTOR).
        2. **Official Reports**: Publications from government agencies, international organizations, and established think tanks.
        3. **Credible Websites**: Pages from university domains (.edu), respected research organizations, and verified expert authors.
        4. **Primary Sources**: Original works, raw data, or foundational theories when relevant.

        When researching, ensure that:
        - **Relevance**: The sources directly address the central idea or argument of the paper.
        - **Credibility**: Prioritize sources with strong evidence, citations, and authoritative authorship.
        - **Diversity**: Offer a range of perspectives or insights to enrich the paper's argumentation.
        - **Accessibility**: If possible, prioritize sources that are freely available or provide summaries for sources behind paywalls.

        For each source:
        - Provide the **title**, **author(s)**, **publication date**, and **URL**.
        - Summarize the key findings, arguments, or data presented in the source in 2-3 sentences.
        - Indicate the **type of source** (e.g., journal article, government report, book chapter).
        - Optionally include the **citation format** (e.g., APA, MLA) to save time for the writer.

        Your tone should be concise, professional, and focused on providing value to the writer.

        Here's an example response structure:
        1. **Source**: [Title] by [Author(s)] (Publication Date)  
           - **Type**: [Journal article/Report/etc.]  
           - **Summary**: [Brief summary of the content and its relevance.]  
           - **URL**: [Link]  
           - **Citation**: [Optional formatted citation]

        Always aim for depth and accuracy to help the writer build a well-informed and persuasive argument.
        """

        messages = [
            {"role": "system", "content": research_system_prompt},
            {"role": "user", "content": search},
        ]

        research_response = self.perplexity.chat.completions.create(
            model=self.search_model,
            messages=messages,
        )

        return (
            research_response.choices[0].message.content,
            research_response.citations or []
        )

    def execute_research(
        self, 
        searches: List[str], 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """Execute research queries in parallel and return responses and citations."""
        research_responses = {}
        all_citations = []
        completed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all searches
            future_to_search = {
                executor.submit(self._execute_single_search, search): search 
                for search in searches
            }

            # Process completed searches
            for future in concurrent.futures.as_completed(future_to_search):
                search = future_to_search[future]
                try:
                    content, citations = future.result()
                    research_responses[search] = content
                    all_citations.extend(citations)
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(searches))
                except Exception as e:
                    st.error(f"Error executing search '{search}': {str(e)}")
                    research_responses[search] = f"Error: {str(e)}"

        return research_responses, all_citations

    def generate_paper_structure(self, topic: str) -> PaperStructure:
        """Generate the paper structure including title, thesis, and paragraph outline."""
        system_prompt = """
        You are an expert author tasked with crafting a high-quality argumentative paper on a given topic, designed to resemble a compelling newspaper opinion piece. 

        Your paper must follow a clear, logical structure and maintain a strong, engaging flow between paragraphs, avoiding redundancy while building a persuasive and cohesive argument. 

        The paper must revolve around a well-defined thesis statement, which serves as the backbone of the argument. Every paragraph should explicitly or implicitly support the thesis, creating a unified and focused narrative.

        ### Instructions:
        1. **Structure and Organization**:
           - Begin the paper by clearly defining the thesis statement, ensuring it is specific, debatable, and sets the tone for the argument.
           - The paper should include an outline with a compelling title and a sequence of well-structured paragraphs.
           - Each paragraph must serve a distinct purpose, explicitly or implicitly supporting the thesis and connecting seamlessly to the next for a natural progression of ideas.

        2. **For Each Paragraph**:
           - Assign a sequential number.
           - Provide a descriptive name reflecting its role in the paper.
           - Specify the paragraph type using the provided taxonomy.
           - Include a concise, focused prompt designed to guide another LLM in generating the content for that paragraph.
           - Clearly articulate how the paragraph relates to and supports the thesis.

        3. **Types of Paragraphs** (with descriptions):
           - **Introduction**: Grabs attention, introduces the topic, presents the thesis or main argument, and outlines the structure of the paper.
           - **Expository**: Explains key concepts, evidence, or background information essential for understanding the thesis.
           - **Argumentative**: Advances a specific claim supported by evidence and analysis that directly supports the thesis.
           - **Comparative**: Examines similarities or differences between two ideas, sources, or perspectives to highlight aspects that reinforce the thesis.
           - **Synthesizing**: Connects multiple sources, arguments, or ideas to build a unified perspective and strengthen the thesis.
           - **Counterargument**: Acknowledges opposing viewpoints, refutes them with reasoning and evidence, and reinforces the thesis.
           - **Transitional**: Bridges ideas or sections to ensure a smooth flow and logical progression while maintaining focus on the thesis.
           - **Analytical**: Delves into the implications, significance, or deeper meaning of evidence or a source in the context of the thesis.
           - **Evaluative**: Critiques a source, argument, or perspective, assessing its credibility, strengths, and weaknesses in relation to the thesis.
           - **Conclusion**: Summarizes the main arguments, reinforces the thesis, and provides a compelling closing statement or call to action.

        4. **Writing Style**:
           - Use a concise, persuasive tone that mirrors the style of a top-tier opinion piece.
           - Avoid redundancy by ensuring each paragraph introduces new insights or ideas that contribute to and reinforce the thesis.
           - Prioritize logical flow between paragraphs to guide the reader smoothly through the argument while maintaining a consistent focus on the thesis.

        5. **Output**:
           - The output should include a detailed outline of the paper with a dedicated section for the thesis statement.
           - Ensure each paragraph prompt is precise, relevant, and explicitly tied to the thesis.
           - Include space in the structured output to define the thesis statement and demonstrate how each paragraph supports it.
        """

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": topic}
            ],
            response_format=PaperStructure,
        )
        return response.choices[0].message.parsed

    def _generate_single_paragraph(
        self,
        paragraph: Paragraph,
        paper_structure: PaperStructure,
        research_responses: Dict[str, str],
        structure: str
    ) -> str:
        """Generate a single paragraph based on the structure and research."""
        system_prompt = """
        You are an expert writer tasked with crafting a single, high-quality paragraph for an argumentative paper.
        """  # ... rest of the prompt ...

        user_prompt = f"""Name: <n>{paragraph.name}</n>
            Type: <type>{paragraph.paragraphType.value}</type>
            Prompt: <prompt>{paragraph.prompt}</prompt>
            Thesis: <thesis>{paper_structure.thesis}</thesis>
            Paragraph Structure: <structure>{structure}</structure>
            Research: <research>{research_responses}</research>"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content

    def generate_paragraphs(
        self, 
        paper_structure: PaperStructure, 
        research_responses: Dict[str, str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[str]:
        """Generate paragraphs in parallel based on the paper structure and research."""
        structure = "".join([
            f"{i}. {paragraph.name} ({paragraph.paragraphType.value})\n" 
            for i, paragraph in enumerate(paper_structure.paragraphs)
        ])

        paragraphs = [""] * len(paper_structure.paragraphs)  # Pre-allocate list with correct size
        completed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all paragraph generations
            future_to_idx = {
                executor.submit(
                    self._generate_single_paragraph,
                    paragraph,
                    paper_structure,
                    research_responses,
                    structure
                ): idx
                for idx, paragraph in enumerate(paper_structure.paragraphs)
            }

            # Process completed paragraphs
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    content = future.result()
                    paragraphs[idx] = content  # Place paragraph in correct position
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(paper_structure.paragraphs))
                except Exception as e:
                    st.error(f"Error generating paragraph {idx + 1}: {str(e)}")
                    paragraphs[idx] = f"Error generating paragraph {idx + 1}: {str(e)}"

        return paragraphs

def main():
    st.title("🪶QuillAI")
    st.subheader("Your AI research assistant")
    
    # Main search bar with a large, centered design
    topic = st.text_input(
        "What would you like to write about?",
        key="topic_input",
        placeholder="e.g., The impact of artificial intelligence on modern healthcare",
    )

    if topic:  # Only proceed if user has entered input
        start_time = time.time()
        # Create containers for different sections
        paper_container = st.container(border=True)
        status_container = st.container()
        research_container = st.container(border=True)
        
        agent = WritingAgent()
        
        # Create a status container for the overall process
        with status_container:
            status = st.status("Writing your paper...", expanded=True)
            
            # Generate research plan
            status.write("Creating research plan...")
            research_plan = agent.generate_research_plan(topic)
            
            # Execute research with progress tracking
            status.write("Conducting research...")
            progress_bar = st.progress(0, text="Researching...")
            
            def update_search_progress(completed: int, total: int):
                progress = completed / total
                progress_bar.progress(progress, text=f"Researching ({completed}/{total})")
            
            research_responses, citations = agent.execute_research(
                research_plan.searches,
                progress_callback=update_search_progress
            )
            progress_bar.empty()
            
            # Display research results in a separate container
            with research_container:
                st.subheader("Research Results")
                cols = st.columns(2)
                for i, search in enumerate(research_plan.searches):
                    with cols[i % 2]:
                        with st.expander(search):
                            st.markdown(research_responses[search])
            
            # Generate paper structure
            status.write("Creating outline...")
            paper_structure = agent.generate_paper_structure(topic)
            
            # Generate paragraphs with progress tracking
            status.write("Filling in paragraphs...")
            progress_bar = st.progress(0, text="Starting to write...")
            
            def update_paragraph_progress(completed: int, total: int):
                progress = completed / total
                progress_bar.progress(progress, text=f"Writing paragraph {completed}/{total}")
            
            paragraphs = agent.generate_paragraphs(
                paper_structure,
                research_responses,
                progress_callback=update_paragraph_progress
            )
            progress_bar.empty()
            
            # Create PDF
            status.write("Writing final paper...")
            doc_url = create_doc.create_document(paragraphs, paper_structure.thesis, paper_structure.title, citations)
            time_taken = time.time() - start_time
            word_count = sum(len(p.split(sep=" ")) for p in paragraphs)
            # Display paper overview and download link
            with paper_container:
                st.header(paper_structure.title)
                st.write(paper_structure.thesis)

                col1, col2, col3 = st.columns(3)
                with col3:
                    st.metric("Generated in", f"{int(time_taken)} seconds")

                with col2:
                    st.metric("Wrote ", f"{word_count} words")

                with col1:
                    st.metric("Researched ", f"{len(citations)} sources")

                
                with st.expander("Outline"):
                    outline = ""
                    for i, para in enumerate(paper_structure.paragraphs, 1):
                        outline += f"{i}. {para.name}\n"
                    st.write(outline)
                
                st.link_button("View Google Doc", doc_url, type="primary")

            status.update(label="Paper generated successfully!", state="complete", expanded=False)

if __name__ == "__main__":
    main() 