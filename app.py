"""
app.py
-------
Gradio application entry point.
All logic lives in ui/ and services/ - this file only assembles the layout,
applies the theme, and wires up event handlers.
"""

import gradio as gr

from ui.components import (
    chatbot, topic_input, search_btn, session_state,
    source_checkboxes, feedback_input,
    approve_btn, reject_btn,
)
from ui.handlers import handle_search, handle_approve, handle_reject

_HITL_OUTPUTS = [source_checkboxes, feedback_input, approve_btn, reject_btn]

# ── Look & feel ───────────────────────────────────────────────────────────────
THEME = gr.themes.Soft(
    primary_hue="emerald",
    secondary_hue="teal",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
#app-header {
    text-align: center;
    padding: 22px 0 6px;
}
#app-header h1 { margin: 0; font-size: 1.7rem; letter-spacing: -0.5px; }
#app-header p { margin: 6px 0 0; color: var(--body-text-color-subdued); }
.hint-row { color: var(--body-text-color-subdued); font-size: 0.9em; }
footer { display: none !important; }
"""

with gr.Blocks(title="Source Scout") as demo:
    gr.HTML(
        """
        <div id="app-header">
            <h1>🧭 Source Scout</h1>
            <p>Give it a topic. It scouts the web, you decide which sources to keep —
            approve the good ones or send it back with feedback.</p>
        </div>
        """
    )

    # Components are built in ui/components.py (outside this Blocks context),
    # so Gradio 6 needs an explicit .render() to place each one in the layout.
    session_state.render()
    chatbot.render()

    with gr.Row():
        topic_input.render()
        search_btn.render()

    source_checkboxes.render()
    feedback_input.render()

    with gr.Row():
        approve_btn.render()
        reject_btn.render()

    _search_outputs = [
        chatbot, session_state, topic_input, search_btn,
        *_HITL_OUTPUTS,
    ]

    search_btn.click(
        fn=handle_search,
        inputs=[topic_input, session_state, chatbot],
        outputs=_search_outputs,
    )
    topic_input.submit(
        fn=handle_search,
        inputs=[topic_input, session_state, chatbot],
        outputs=_search_outputs,
    )

    approve_btn.click(
        fn=handle_approve,
        inputs=[source_checkboxes, session_state, chatbot],
        outputs=[chatbot, session_state, *_HITL_OUTPUTS],
    )

    reject_btn.click(
        fn=handle_reject,
        inputs=[feedback_input, session_state, chatbot],
        outputs=[chatbot, session_state, *_HITL_OUTPUTS],
    )


if __name__ == "__main__":
    # Gradio 6 takes theme + css on launch(), not on Blocks().
    demo.launch(theme=THEME, css=CSS)
