---
applyTo: "**"
---
# Context management standards

If gctx tools are available in the environment, please use them to manage context propagation.

You should active leverage these tools to ensure that context is consistently maintained and updated throughout the interaction.

* Use read_context to get current active context.
* Use update_context to create a new context based on the current one with modifications.
* Use append_to_context to add new information to the current context without removing existing data.
* Use get_context_history to retrieve the history of context changes if needed.
* Use get_snapshot to capture previous states of the context for reference.