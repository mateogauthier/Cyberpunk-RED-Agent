# Cyberpunk RED Agent Chatbot

This project aims to create a chatbot simulating an Agent from the Cyberpunk RED TTRPG universe. The goal is to develop an interactive AI experience that embodies the tone, jargon, and moral ambiguity of the genre.

## 🚀 Getting Started

Follow these steps to get the project up and running.

### Prerequisites

*   Python 3.8+
*   `pip`
*   A conceptual understanding of Cyberpunk RED lore.

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd cyberpunk-agent-bot
    ```
2.  Set up a virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```
4.  Create a `.env` file in the project root:
    ```env
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=llama3.2
    ```
5.  Start the API server:
    ```bash
    uvicorn code.api_server:app --reload
    ```
    Interactive docs available at `http://localhost:8000/docs`.

## 🤖 Project Structure

The core logic, character definitions, and interaction scripts will reside in the following structure:

*   `agents.md`: Detailed profiles and background lore for potential agents/personas.
*   `specifications.md`: The operational guidelines, conversational rules, and technical constraints for the chatbot.
*   `main.py`: The primary entry point for the chatbot interface.
*   `utils/`: Helper functions, character asset storage, lore databases, etc.

## ✨ Goals

*   **Immersion:** Generate responses that feel authentic to the setting (corporate paranoia, street-level grit, chrome, etc.).
*   **Roleplay Accuracy:** Maintain a consistent persona based on the chosen Agent profile.
*   **Expandability:** Allow for easy addition of new lore, mechanics, and character archetypes.

## 💡 Initial Tasks

1.  Define core lore parameters in `specifications.md`.
2.  Populate character profiles in `agents.md`.
3.  Build the initial conversational wrapper in `main.py`.

---
*Developed with a healthy dose of Black ICE and bad decisions.*