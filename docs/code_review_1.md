Here is a detailed code review.

### Overall Assessment

This is a sophisticated and powerful research agent project. The dual-architecture approach (Graph-based vs. Multi-Agent) is impressive, and the level of documentation (`README.md`, `docs/`) is very good. The project is clearly mature, with support for various models, search APIs, and a robust testing/evaluation framework.

The primary issues stem from the integration of a highly specific, custom requirement (the WBG authentication and endpoints) into a generic, open-source framework. This has created some architectural conflicts, configuration inconsistencies, and hidden behaviors that need to be addressed.

---

### 🚨 Critical Issues to Fix

These are items that are likely broken, behave in unexpected ways, or represent significant functional gaps.

 1. Dueling Authentication Systems: `api_keys` are Ignored for WBG Models 

*    Problem:  The system has two separate authentication managers: the generic `AuthManager` (`auth.py`) and the specific `WBGAuthManager` (`wbg_auth_manager.py`). The `api_adapter.py` is designed to switch between them. However, when it detects a WBG model (`provider == "wbg"`), it completely bypasses the generic `AuthManager` and the `api_keys` dictionary from your configuration.
*    File:  `src/open_deep_research/wbg_llm_adapter.py`
*    Code: 
    ```python
    class WBGChatModel(SimpleChatModel):
        # ...
        # This ALWAYS creates a new WBGAuthManager, ignoring any other auth system.
        auth_manager: WBGAuthManager = Field(default_factory=WBGAuthManager, exclude=True)
    ```
*    Impact:  This is misleading and a potential bug. A user might configure `api_keys` in their script or `.env` file, but for WBG models, these keys will be  silently ignored . The system will *always* use the `WBGAuthManager`'s token cache (`.wbg_token_cache.bin`). This breaks the principle of least surprise and makes configuration difficult to debug.
*    Fix:  The `create_wbg_llm` factory should not instantiate its own `WBGAuthManager`. It should be passed in or managed by the central `api_adapter.py`, just like the generic models. The system needs a single, unified way to handle authentication.

 2. Multi-Agent Search API is Severely Limited 

*    Problem:  The multi-agent implementation explicitly raises a `NotImplementedError` for any search API other than Tavily, DuckDuckGo, or WBG Google. This contradicts the `SearchAPI` enum in `configuration.py` which lists many more options (Perplexity, Exa, etc.).
*    File:  `src/open_deep_research/multi_agent.py`
*    Code: 
    ```python
    def get_search_tool(config: RunnableConfig):
        # ...
        if search_api.lower() == "tavily":
            search_tool = tavily_search
        elif search_api.lower() == "duckduckgo":
            search_tool = duckduckgo_search
        elif search_api.lower() == "wbg_google":
            search_tool = wbg_google_search
        else:
            raise NotImplementedError(
                f"The search API '{search_api}' is not yet supported in the multi-agent implementation..."
            )
    ```
*    Impact:  This is a broken feature. If a user configures the multi-agent system to use `SearchAPI.EXA`, the program will crash. The graph-based implementation appears to be more flexible.
*    Fix:  Implement the other search tools for the multi-agent system or, at a minimum, update the documentation and configuration files to make this limitation crystal clear.

 3. The CLI only supports the Multi-Agent Implementation 

*    Problem:  The `cli.py` script exclusively calls `run_multi_agent`. There is no command-line flag or option to run the graph-based workflow.
*    File:  `src/open_deep_research/cli.py`
*    Code: 
    ```python
    # ...
    from .agent import run_multi_agent
    # ...
    report = run_multi_agent(prompt, auto_accept_plan=args.auto_accept_plan)
    ```
*    Impact:  A major feature of the application (the graph-based workflow) is inaccessible from the primary user interface (the CLI).
*    Fix:  Add a new argument to the CLI, such as `--agent-type {graph,multi-agent}`, to allow the user to select which implementation to run.

 4. Unused `use_wbg_models` Configuration Flag 

*    Problem:  Both `WorkflowConfiguration` and `MultiAgentConfiguration` in `src/open_deep_research/configuration.py` have a `use_wbg_models: bool = True` flag. However, a project-wide search shows this flag is  never actually used . The decision to use WBG models is based purely on the model/provider name (e.g., `"wbg:o4-mini"`).
*    Impact:  This is dead code. It gives a false impression of a feature that doesn't exist, potentially confusing users who try to set it to `False`.
*    Fix:  Either remove this flag from the configuration classes or implement logic that uses it to conditionally switch between WBG and public models.

---

### 🧱 Important Architectural & Code Quality Suggestions

These are not outright bugs but represent significant architectural inconsistencies or maintainability issues.

 1. Confusing Project Structure: `src/open_deep_research/workflow/` Directory 

*    Problem:  There is a directory `src/open_deep_research/workflow` containing its own `configuration.py`, `prompts.py`, `state.py`, and `workflow.py`. This seems to be a complete, self-contained, and slightly different version of the graph-based implementation. It creates massive confusion about which version of the code is authoritative.
*    Impact:  It's unclear what this directory's purpose is. Is it a legacy version? An alternative implementation? A developer could easily edit the wrong files. For example, `src/open_deep_research/graph.py` imports from the root `configuration.py`, not `workflow/configuration.py`.
*    Recommendation:  DELETE THIS DIRECTORY.

 2. Inconsistent Configuration Styles 

*    Problem:  The two architectures use different styles for configuring models.
    *    Multi-Agent:  Uses a single string: `supervisor_model: str = "wbg:o4-mini"`.
    *    Graph-based:  Uses separate provider and model fields: `planner_provider: str = "wbg"` and `planner_model: str = "o4-mini"`.
*    Impact:  This makes it harder to switch between architectures and creates a mental burden for the user. A unified configuration approach would be much better.
*    Recommendation:  Standardize on one format. The `provider:model_name` format is generally more robust and is what `init_chat_model` already supports.

 3. Hardcoded WBG Defaults and Token Limits 

*    Problem:  The `configuration.py` file hardcodes the default models and search provider to the WBG-specific ones. The WBG token limit (`wbg_max_tokens: int = 100000`) is defined in the configuration but also seems to be hardcoded as a default in the `create_wbg_llm` function in `wbg_llm_adapter.py`.
*    Impact:  This makes the "open-source" framework feel very tailored to one specific deployment, reducing its general-purpose utility. The redundant token limit definition is brittle.
*    Recommendation:  Move the WBG-specific defaults to an example `.env` file or a separate configuration file (e.g., `config.wbg.yaml`). The `create_wbg_llm` function should always pull the token limit from the configuration object passed to it, not have its own default.


4. CLI Flexibility:  The CLI doesn't allow overriding model configurations via flags. For development and testing, it would be useful to run `odr --country "Angola" --supervisor-model "openai:gpt-4.1-turbo"`.
5. Unnecessary CLI Wrapper:  `cli.py` in the root is a wrapper for `src/open_deep_research/cli.py`. If the package is installed correctly (`pip install -e .`), the `odr` entry point in `pyproject.toml` makes the wrapper script redundant. It's fine for convenience but could be clarified in the docs.
6. FinishResearch Tool:  In `multi_agent.py`, `FinishResearch` is a Pydantic `BaseModel` used as a signal to end the research loop. A more common LangGraph pattern is to use the content of a message or a specific field in the state to drive conditional edges, which can be slightly cleaner than defining a no-op tool. This is a stylistic point, and the current implementation works.
