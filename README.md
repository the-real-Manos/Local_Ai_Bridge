# Local_Ai_Bridge
Chat Bridge: Allows LM studio to communicate via locally hosted webpage. Suitable for desktop and mobile

A lightweight, mobile-friendly web interface for interacting with local LLMs running via LM Studio. 

## Features
* Mobile Ready: Includes a built-in QR code generator to easily connect your phone to your local PC's AI.
* Canvas: Open code snippets in a side panel to edit, experiment, or copy without cluttering the chat.
* Theme Support: Dark and Light mode toggles.
* Real-time Streaming: See the AI response as it generates.
* Local History: Chat history is saved to your browser's local storage. Can be cleared.
* Copy Chat: Copy reponses
* Dark mode: Aesthetic choice 
* Share link with QR code

---

## Prerequisites

### LM Studio
1.  **Download & Install:** Get [LM Studio](https://lmstudio.ai/) for Windows, Mac, or Linux.
2.  **Enable Power User / Developer Mode:** Open LM Studio.
click on the **Developer/Local Server** tab (the `<->` icon on the left sidebar).
3.  **Load a Model:** Select a model from the top dropdown and wait for it to finish loading.
4.  **Start Server:**
    * Ensure the **Port** is set to `1234` (this is the default the bridge looks for).
    * Turn **Cross-Origin Resource Sharing (CORS)** to `ON`.
    * Click the **Status** button. Ensure it is running.

### Python Environment
Ensure you have Python 3.8+ installed. You will need to install the following dependencies:

fastapi uvicorn httpx qrcode[pil]


## Project Structure
.

├── main.py

└── static/

## Setup

python main.py
