# Human Skill Digital Twin - Plugin SDK Guide

The platform includes a built-in Plugin SDK (`app/sdk/plugin_sdk.py`) enabling developers to extend capabilities: custom analytical dashboards, new spaced repetition models, custom event-driven agents, or alternative learning path heuristics.

---

## 1. Registering Custom Memory Decay Models

You can register custom models (like Leitner flashcard queues or Halflife regression decay rates) by using the `@plugin_sdk.register_memory_model` decorator.

```python
from backend.app.sdk.plugin_sdk import plugin_sdk
from datetime import datetime, timedelta

@plugin_sdk.register_memory_model("leitner_box")
def calculate_leitner_intervals(current_box: int, was_correct: bool) -> int:
    """Calculates days until next check based on Leitner boxes (1 to 5)."""
    if was_correct:
        next_box = min(5, current_box + 1)
    else:
        next_box = 1
        
    intervals_map = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    return intervals_map[next_box]
```

---

## 2. Registering Event-Driven Agents

To build a custom agent that reacts to platform actions (e.g. logging stats to an external analytics API when a user masters a concept):

```python
from backend.app.sdk.plugin_sdk import plugin_sdk
from backend.app.core.events import event_broker

class SlackNotificationAgent:
    def __init__(self):
        # Subscribe direct handler to event loop
        event_broker.subscribe("assessment.completed", self.on_quiz_finished)

    async def on_quiz_finished(self, payload: dict):
        score = payload.get("score")
        if score > 0.9:
            # Code to send congrats notification to Slack hook
            print(f"[SlackAgent] Hurray! Concept {payload.get('concept_id')} mastered with score {score}")

# Instantiate to activate subscription
slack_agent = SlackNotificationAgent()
```

---

## 3. Customizing Dashboard Panels

Register custom layout metadata that backend API routers can expose to modular frontend components:

```python
from backend.app.sdk.plugin_sdk import plugin_sdk

@plugin_sdk.register_dashboard_view("focus_matrix")
def generate_matrix_view(user_id: int) -> dict:
    """Returns coordinates data to build a custom study scatter plot."""
    return {
        "x_axis": "focus_hours",
        "y_axis": "mastery_gain",
        "points": [
            {"x": 2.5, "y": 0.12, "label": "Basics"},
            {"x": 5.0, "y": 0.35, "label": "Deep Learning"}
        ]
    }
```
# Extensibility checklist
To load a plugin module automatically during backend startup, import it in `backend/app/main.py` before initializing uvicorn.
