"""
ui/components.py
─────────────────
Defines all Gradio UI components as module-level objects
so they can be shared between layout and event handlers.
"""

import gradio as gr

# Gradio 6 Chatbot is messages-only: a list of {"role", "content"} dicts.
chatbot = gr.Chatbot(label="Research thread", height=520)

topic_input = gr.Textbox(
    placeholder="e.g. Artificial Intelligence in healthcare",
    label="What should I research?",
    scale=5,
)

search_btn = gr.Button("Find sources", variant="primary", scale=1)

source_checkboxes = gr.CheckboxGroup(
    label="Sources found — keep the ones you want",
    info="Uncheck anything you want to drop, then approve.",
    visible=False,
    interactive=True,
)

feedback_input = gr.Textbox(
    placeholder="Explain what was wrong and what you need instead…",
    label="Feedback for a new search",
    visible=False,
    lines=2,
)

approve_btn = gr.Button("Approve selected", variant="primary", visible=False)
reject_btn = gr.Button("Reject & search again", variant="secondary", visible=False)

session_state = gr.State({})
