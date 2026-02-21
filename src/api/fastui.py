from typing import List

from fastapi.responses import HTMLResponse
from fastui import AnyComponent, components as c, prebuilt_html
from fastui.events import GoToEvent


def ui_root() -> List[AnyComponent]:
    return [
        c.Page(
            components=[
                c.Heading(text="Malicious Content Detection", level=2),
                c.Paragraph(
                    text="Use the React UI for analysis or call the API directly."
                ),
                c.Link(
                    components=[c.Text(text="Open React UI")],
                    on_click=GoToEvent(url="/"),
                ),
            ]
        )
    ]


def ui_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title="Malicious Content Detection"))
