"""Example of using the new API key authentication system with Open Deep Research."""

import asyncio
from dotenv import load_dotenv
from open_deep_research.graph import graph
from open_deep_research.multi_agent import graph as multi_agent_graph
from open_deep_research.auth import AuthManager
from open_deep_research.api_adapter import set_global_auth_manager

# Load environment variables (for backward compatibility)
load_dotenv()


async def example_with_env_vars():
    """Example using environment variables (backward compatible)."""
    print("=== Example 1: Using Environment Variables ===")
    print("This is the traditional way - set API keys in .env file")
    print("No code changes needed!\n")
    
    # The graphs will automatically use environment variables
    topic = "The impact of artificial intelligence on healthcare"
    
    # Using graph-based implementation
    async for chunk in graph.astream(
        {"topic": topic},
        {"configurable": {"writer_model": "gpt-4"}}
    ):
        print(f"Graph progress: {list(chunk.keys())}")


async def example_with_config_api_keys():
    """Example passing API keys through configuration."""
    print("\n=== Example 2: Using Configuration API Keys ===")
    print("Pass API keys directly in configuration - no env vars needed!\n")
    
    # Define API keys
    api_keys = {
        "openai": "your-openai-api-key-here",
        "anthropic": "your-anthropic-api-key-here",
        "google_genai": "your-google-api-key-here"
    }
    
    topic = "Latest developments in quantum computing"
    
    # Using graph-based implementation with API keys in config
    async for chunk in graph.astream(
        {"topic": topic},
        {"configurable": {
            "planner_model": "gemini-1.5-pro",
            "writer_model": "gpt-4",
            "api_keys": api_keys  # Pass API keys here
        }}
    ):
        print(f"Graph progress: {list(chunk.keys())}")


async def example_with_global_auth_manager():
    """Example using a global AuthManager."""
    print("\n=== Example 3: Using Global AuthManager ===")
    print("Set up authentication once, use everywhere!\n")
    
    # Create and configure a global auth manager
    auth_manager = AuthManager(api_keys={
        "openai": "your-openai-api-key-here",
        "anthropic": "your-anthropic-api-key-here",
        "google_genai": "your-google-api-key-here"
    })
    
    # Set it globally
    set_global_auth_manager(auth_manager)
    
    # Now all model initializations will use these keys automatically
    topic = "The future of renewable energy"
    
    # Using multi-agent implementation
    async for chunk in multi_agent_graph.astream(
        {"messages": [{"role": "user", "content": f"Research this topic: {topic}"}]},
        {"configurable": {
            "supervisor_model": "anthropic:claude-3-opus",
            "researcher_model": "openai:gpt-4"
        }}
    ):
        print(f"Multi-agent progress: {list(chunk.keys())}")


async def example_mixed_auth():
    """Example mixing different authentication methods."""
    print("\n=== Example 4: Mixed Authentication ===")
    print("Use env vars for some providers, config for others\n")
    
    # Assume OPENAI_API_KEY is in .env, but we'll provide others via config
    api_keys = {
        "anthropic": "your-anthropic-api-key-here",
        "google_genai": "your-google-api-key-here"
    }
    
    topic = "Blockchain applications in supply chain management"
    
    # The system will use:
    # - Environment variable for OpenAI
    # - Config keys for Anthropic and Google
    async for chunk in graph.astream(
        {"topic": topic},
        {"configurable": {
            "planner_model": "claude-3-opus",      # Uses config key
            "writer_model": "gpt-4",               # Uses env var
            "summarization_model": "gemini-1.5-flash",  # Uses config key
            "api_keys": api_keys
        }}
    ):
        print(f"Graph progress: {list(chunk.keys())}")


async def example_provider_specific():
    """Example showing provider-specific authentication."""
    print("\n=== Example 5: Provider-Specific Features ===")
    print("Different providers have different auth requirements\n")
    
    # Create auth manager with various provider keys
    auth_manager = AuthManager()
    
    # Standard API key providers
    auth_manager.set_api_key("openai", "sk-...")
    auth_manager.set_api_key("anthropic", "sk-ant-...")
    
    # Providers that don't need API keys
    # Ollama runs locally - no key needed
    print(f"Ollama needs auth: {auth_manager.has_auth_for_provider('ollama')}")  # False
    
    # AWS Bedrock uses AWS credentials (from env vars or ~/.aws/credentials)
    # The auth system will automatically pick these up
    print(f"Bedrock auth check: {auth_manager.has_auth_for_provider('bedrock')}")
    
    # You can check what auth kwargs will be passed
    print(f"OpenAI auth kwargs: {auth_manager.get_auth_kwargs('openai')}")
    print(f"Ollama auth kwargs: {auth_manager.get_auth_kwargs('ollama')}")


def main():
    """Run all examples."""
    print("Open Deep Research - API Key Authentication Examples")
    print("=" * 50)
    print("\nNOTE: Replace 'your-xxx-api-key-here' with actual API keys!\n")
    
    # Uncomment the examples you want to run:
    
    # asyncio.run(example_with_env_vars())
    # asyncio.run(example_with_config_api_keys())
    # asyncio.run(example_with_global_auth_manager())
    # asyncio.run(example_mixed_auth())
    asyncio.run(example_provider_specific())


if __name__ == "__main__":
    main()