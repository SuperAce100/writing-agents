# Hierarchical Multi-Agent Systems for Automated Academic Writing

## Research Overview

This project explores the application of hierarchical multi-agent systems to complex cognitive tasks, specifically academic writing. By decomposing the writing process into specialized agent roles, the system demonstrates how emergent behaviors can arise from structured agent interactions while maintaining coherence through typed constraints.

## Agent Architecture
The system employs a hierarchical agent architecture based on three key theoretical principles:

1. **Specialization with Bounded Rationality**
   - Each agent operates within a specifically defined domain
   - Decision-making is constrained by explicit schemas
   - Information flow is structured through typed interfaces

2. **Emergent Coordination**
   - Agents interact through a mediator-based architecture
   - Higher-level agents provide strategic direction
   - Lower-level agents handle tactical execution

3. **Constrained Generation with Validation**
   - Output generation is bounded by formal specifications
   - Cross-validation occurs at agent boundaries
   - Schema enforcement ensures coherent composition

## Experimental Results

The system demonstrates several key capabilities:

1. **Task Decomposition**
   - Successfully breaks down complex writing tasks
   - Maintains coherence across subtasks
   - Produces well-structured academic content

2. **Knowledge Integration**
   - Effectively incorporates research findings
   - Maintains citation consistency
   - Preserves academic rigor

3. **Quality Metrics**
   - Output adheres to academic standards
   - Arguments maintain logical flow
   - Citations are properly integrated



## Environment Setup

This guide will help you set up the necessary environment and credentials for the Writing Agents project.

### Prerequisites

- Python 3.7 or higher
- A Google Cloud Platform account
- An OpenAI API key
- A Perplexity API key

### Installation

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   conda create -n writing-agents python=3.9
   conda activate writing-agents
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### API Keys Setup

1. Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_key_here
   PERPLEXITY_API_KEY=your_perplexity_key_here
   ```

2. Google Cloud Setup:
   - Create a new project in Google Cloud Console
   - Enable the Google Docs API and Google Drive API
   - Create a service account:
     1. Go to IAM & Admin > Service Accounts
     2. Click "Create Service Account"
     3. Give it a name and grant it the following roles:
        - Google Docs API > Docs Editor
        - Google Drive API > Drive Editor
   - Create and download the service account key (JSON)
   - Place the JSON key file in `./keys/NAME_OF_THE_SERVICE_ACCOUNT.json`

## Usage

See `writing.ipynb` for usage.
