---
applyTo: "**"
---
# Context Management Standards

If gctx MCP tools are available, actively use them to manage context across sessions. These tools provide Git-based context versioning with token pressure monitoring.
You can actively offload the conversation to gctx-managed context, allowing for better organization and compression when token limits are approached.

**At session start:**
- Use `read_context()` to restore context state and check token metrics
- Monitor `token_pressure_percentage` to decide when compression is needed

**During work:**
- Use `append_to_context(text, message)` for incremental updates (logs, findings, progress)
- Use `update_context(new_context, message)` when compressing or restructuring context
- Check `success` field in all results before using other fields

**For historical reference:**
- Use `get_context_history(limit, starting_after)` to view past commits
- Use `get_snapshot(commit_sha)` to retrieve content from specific commits
- Use `search_context_history(keywords, limit)` to search commits by keywords in messages or content
- Review history before compression to avoid losing important information

**Best practices:**
- Always check `success` field; handle errors via `error` field
- Use descriptive commit messages for easier history navigation and searchability
- Consider compression when `token_pressure_percentage` > 0.8
- Use search to quickly find relevant past context without reviewing all history