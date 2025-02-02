# Hierarchical Multi-Agent Systems for Automated Academic Writing

## Research Overview

This project explores the application of hierarchical multi-agent systems to complex cognitive tasks, specifically academic writing. By decomposing the writing process into specialized agent roles, the system demonstrates how emergent behaviors can arise from structured agent interactions while maintaining coherence through typed constraints.

## Theoretical Framework

### Agent Architecture
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

## Research Contributions

### Novel Aspects of the Architecture

1. **Hierarchical Planning Decomposition**
   - Research tasks are decomposed through a planning hierarchy
   - Each level maintains its own representation space
   - Information is aggregated through structured channels

2. **Type-Theoretic Agent Boundaries**
   - Agent interfaces are defined through formal type systems
   - Communication protocols enforce semantic consistency
   - Error handling is managed through type validation

3. **Emergence Through Constraint Satisfaction**
   - Complex behaviors emerge from simple, constrained interactions
   - Global coherence is maintained through local constraints
   - Type system ensures compositional correctness

### Methodological Innovations

1. **Multi-Level Prompt Engineering**
   - Prompts are structured hierarchically
   - Each level handles different aspects of the task
   - Cross-level consistency is maintained through schemas

2. **Structured Knowledge Integration**
   - Research findings are formally represented
   - Knowledge is integrated through typed interfaces
   - Citations are tracked across agent boundaries

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

## Research Implications

This work has several implications for multi-agent systems research:

1. **Scalability of Agent Architectures**
   - Demonstrates viability of hierarchical decomposition
   - Shows how type systems can ensure coherence
   - Provides framework for complex task automation

2. **Emergent Behaviors**
   - Complex writing emerges from simple agents
   - Local constraints produce global coherence
   - Type systems enable compositional reasoning

3. **Future Directions**
   - Extension to other cognitive tasks
   - Investigation of more complex agent hierarchies
   - Development of richer type systems

## Theoretical Significance

The project contributes to several key areas of AI research:

1. **Multi-Agent Systems Theory**
   - New approaches to agent coordination
   - Type-theoretic foundations for agent interaction
   - Hierarchical planning methodologies

2. **Cognitive Architecture Design**
   - Decomposition of complex cognitive tasks
   - Integration of symbolic and neural approaches
   - Structured knowledge representation

3. **Automated Reasoning**
   - Type-based compositional reasoning
   - Constraint satisfaction in agent systems
   - Emergence through bounded rationality

This research demonstrates how formal methods in multi-agent systems can be applied to complex cognitive tasks, suggesting new directions for AI research in automated content generation and reasoning.


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