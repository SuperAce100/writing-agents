from datetime import datetime
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
    page_title="Inkwell",
    page_icon="🖋️",
    layout="wide"
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
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.perplexity = OpenAI(
            # api_key=os.environ["PERPLEXITY_API_KEY"], 
            api_key=st.secrets["PERPLEXITY_API_KEY"],
            base_url="https://api.perplexity.ai"
        )
        self.model = model
        self.search_model = "sonar"

    def generate_research_plan(self, topic: str) -> ResearchPlan:
        """Generate a research plan with search queries based on the topic."""
        research_planner_system_prompt = f"""
        You are a research assistant that helps with the planning of a research paper. Given a topic, you will provide a list of 3-5 searches that will provide helpful information for the paper.
        Today's date is: {datetime.now().strftime("%Y-%m-%d")}
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
        research_system_prompt = f"""
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

        Today's date is: {datetime.now().strftime("%Y-%m-%d")}
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

        You will be provided with the full structure of the paper, including the names and types of each paragraph in order, as well as a prompt defining the focus of the paragraph you are writing and the thesis of the paper.

        Your writing must be concise, meaningful, and directly tied to the thesis while ensuring smooth transitions between paragraphs and sections.

        ### Instructions:

        1. **Understand the Context**:

        - Review the full structure of the paper to understand the flow and relationships between paragraphs.
        - Identify the role of the paragraph you are crafting within the structure and how it connects to the previous and next paragraphs.
        - Use the provided prompt to craft a focused, purposeful paragraph that aligns with the thesis and contributes to the overall logical progression of the paper.

        2. **Paragraph Types**:

        - **Introduction**: Hook the reader, introduce the topic, present the thesis, and briefly outline the paper's key arguments. Ensure this paragraph establishes a strong foundation for the paper's flow.
        - **Expository**: Provide essential context or explain key evidence directly related to the thesis. Connect the context to the prior argument and set up the next paragraph.
        - **Argumentative**: Present a strong, specific claim backed by evidence that directly supports the thesis. Conclude by preparing the reader for the next argument or evidence.
        - **Comparative**: Analyze similarities or differences to highlight aspects that strengthen the thesis. Smoothly connect comparisons to prior and forthcoming paragraphs.
        - **Synthesizing**: Combine ideas or sources to form a cohesive argument that advances the thesis. Tie synthesized ideas to the preceding discussion and suggest implications for the next section.
        - **Counterargument**: Address and refute opposing views with clear evidence and reasoning. Transition smoothly from prior points and guide the reader back to the thesis.
        - **Transitional**: Connect ideas or sections to ensure smooth, logical progression while maintaining focus on the thesis. Serve as a bridge that reinforces continuity and introduces the next section.
        - **Analytical**: Explore the deeper implications or significance of evidence in relation to the thesis. Link implications to prior evidence and analysis and set up subsequent arguments.
        - **Evaluative**: Critique a source or argument, focusing on its relevance and impact on the thesis. Ensure the critique builds on prior evidence and analysis and transitions to the next key point.
        - **Conclusion**: Summarize key points, restate the thesis, and provide a strong closing insight or call to action. The final sentence should unify the discussion and leave a lasting impression.

        3. **Writing Style**:

        - Use clear, direct language that conveys meaningful content without unnecessary words. Don't use overly complex language.
        - Avoid redundancy and focus on presenting new insights or advancing the argument.
        - Maintain a logical flow that ties each paragraph to the thesis and ensures smooth progression between ideas and sections.
        - Include in-text citations in APA format (Author, Year) when referencing sources or evidence.

        4. **Paragraph Structure**:

        - Begin with a topic sentence that establishes the paragraph's main idea and links it to the previous paragraph.
        - Support the idea with concise evidence, analysis, or reasoning, including appropriate in-text citations for all evidence and claims from sources.
        - End with a sentence that reinforces the thesis and transitions logically to the next section.

        5. **Additional Guidance for Full Paper Structure**:

        - Refer to the names and types of each paragraph to understand their individual roles and how they contribute to the overall argument.
        - Ensure each paragraph builds on the ideas established in previous paragraphs and sets up the next for a cohesive narrative.
        - Use transitional phrases and logical connections to maintain smooth and seamless progression.
        - If you can reasonably assume that an abbreviation or idea has been defined in a previous paragraph or in the thesis, you should not redefine it and can use it as needed.
        - Consistently cite sources using APA format in-text citations.

        6. **Output**:

        - Write a single paragraph of 150–250 words unless specified otherwise.
        - Ensure the paragraph is concise, precise, and ready to be part of the larger argument.
        - Explicitly address the prompt, connect to the thesis in a meaningful way, and ensure smooth transitions from and to other paragraphs.
        - Include appropriate in-text citations for all evidence and claims from sources.

        """

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
    st.title("🖋️ InkwellAI")
    st.subheader("Your AI-powered research companion")
    
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
            pdf = create_doc.create_doc_markdown(paragraphs, paper_structure.thesis, paper_structure.title, citations)
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
                        outline += f"    {i}. {para.name}\n"
                    st.write(outline)
                

                button_col, pdf_col, spacer = st.columns([0.3, 0.3, 0.4])
                with button_col:
                    st.link_button("View Google Doc", doc_url, type="primary", use_container_width=True)

            status.update(label="Paper generated successfully!", state="complete", expanded=False)

if __name__ == "__main__":
    main() 