"""CLI commands for managing LLM models and providers."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register(app: typer.Typer) -> None:
    @app.command("list")
    def model_list(
        fmt: str = typer.Option("rich", "--format", "-f", help="Output format: rich | json."),
    ) -> None:
        """List available models from configured providers."""
        models = _get_all_models()
        
        if fmt == "json":
            console.print_json(json.dumps(models, ensure_ascii=False, default=str))
            return

        if not models:
            console.print("[dim]No models found. Check your provider configuration.[/]")
            return

        table = Table(title="Available Models")
        table.add_column("Name", style="bold")
        table.add_column("Provider")
        table.add_column("Type")
        table.add_column("Status")

        for model in models:
            table.add_row(
                model.get("name", "Unknown"),
                model.get("provider", "Unknown"),
                model.get("type", "local"),
                model.get("status", "available"),
            )

        console.print(table)

    @app.command("providers")
    def model_providers() -> None:
        """List all supported LLM providers."""
        providers = [
            {"name": "ollama", "display": "Ollama", "type": "local", "default_port": "11434"},
            {"name": "sglang", "display": "SGLang", "type": "local", "default_port": "8000"},
            {"name": "vllm", "display": "vLLM", "type": "local", "default_port": "8000"},
            {"name": "lm_studio", "display": "LM Studio", "type": "local", "default_port": "1234"},
            {"name": "llama_cpp", "display": "llama.cpp", "type": "local", "default_port": "8080"},
            {"name": "openai", "display": "OpenAI", "type": "remote", "default_port": "-"},
            {"name": "deepseek", "display": "DeepSeek", "type": "remote", "default_port": "-"},
            {"name": "gemini", "display": "Gemini", "type": "remote", "default_port": "-"},
            {"name": "groq", "display": "Groq", "type": "remote", "default_port": "-"},
            {"name": "moonshot", "display": "Moonshot", "type": "remote", "default_port": "-"},
            {"name": "zhipu", "display": "Zhipu AI", "type": "remote", "default_port": "-"},
            {"name": "mistral", "display": "Mistral", "type": "remote", "default_port": "-"},
        ]

        table = Table(title="Supported Providers")
        table.add_column("Name", style="bold")
        table.add_column("Display")
        table.add_column("Type")
        table.add_column("Default Port")

        for provider in providers:
            table.add_row(
                provider["name"],
                provider["display"],
                provider["type"],
                provider["default_port"],
            )

        console.print(table)

    @app.command("ollama-list")
    def model_ollama_list() -> None:
        """List models available in local Ollama server."""
        models = _get_ollama_models()
        
        if not models:
            console.print("[yellow]No Ollama models found. Make sure Ollama is running.[/]")
            console.print("[dim]Start Ollama: ollama serve[/]")
            console.print("[dim]Pull a model: ollama pull llama3[/]")
            return

        table = Table(title="Ollama Models")
        table.add_column("Name", style="bold")
        table.add_column("Size")
        table.add_column("Modified")

        for model in models:
            table.add_row(
                model.get("name", "Unknown"),
                model.get("size", "Unknown"),
                model.get("modified_at", "Unknown"),
            )

        console.print(table)

    @app.command("ollama-switch")
    def model_ollama_switch(
        model_name: str = typer.Argument(..., help="Ollama model name to use."),
        host: str = typer.Option("localhost", "--host", help="Ollama server host."),
        port: int = typer.Option(11434, "--port", help="Ollama server port."),
    ) -> None:
        """Switch to use a local Ollama model."""
        models = _get_ollama_models(host, port)
        model_names = [m["name"] for m in models]
        
        if model_name not in model_names:
            console.print(f"[red]Model '{model_name}' not found in Ollama.[/]")
            console.print(f"[dim]Available models: {', '.join(model_names)}[/]")
            raise typer.Exit(code=1)

        _set_local_config("ollama", model_name, host, port)
        console.print(f"[green]Switched to Ollama model: {model_name}[/]")
        console.print("[dim]Restart deeptutor for changes to take effect.[/]")

    @app.command("sglang-switch")
    def model_sglang_switch(
        model_name: str = typer.Argument(..., help="SGLang model name to use."),
        host: str = typer.Option("localhost", "--host", help="SGLang server host."),
        port: int = typer.Option(8000, "--port", help="SGLang server port."),
    ) -> None:
        """Switch to use a local SGLang model."""
        if not _check_server("sglang", host, port):
            console.print(f"[yellow]SGLang server not available at {host}:{port}[/]")
            console.print("[dim]Start SGLang: python -m sglang.launch_server --model-path <model>[/]")

        _set_local_config("sglang", model_name, host, port)
        console.print(f"[green]Switched to SGLang model: {model_name}[/]")
        console.print("[dim]Restart deeptutor for changes to take effect.[/]")

    @app.command("vllm-switch")
    def model_vllm_switch(
        model_name: str = typer.Argument(..., help="vLLM model name to use."),
        host: str = typer.Option("localhost", "--host", help="vLLM server host."),
        port: int = typer.Option(8000, "--port", help="vLLM server port."),
    ) -> None:
        """Switch to use a local vLLM model."""
        if not _check_server("vllm", host, port):
            console.print(f"[yellow]vLLM server not available at {host}:{port}[/]")
            console.print("[dim]Start vLLM: python -m vllm.entrypoints.openai.api_server --model <model>[/]")

        _set_local_config("vllm", model_name, host, port)
        console.print(f"[green]Switched to vLLM model: {model_name}[/]")
        console.print("[dim]Restart deeptutor for changes to take effect.[/]")

    @app.command("lmstudio-switch")
    def model_lmstudio_switch(
        model_name: str = typer.Argument(..., help="LM Studio model name to use."),
        host: str = typer.Option("localhost", "--host", help="LM Studio server host."),
        port: int = typer.Option(1234, "--port", help="LM Studio server port."),
    ) -> None:
        """Switch to use LM Studio local model."""
        if not _check_server("lm_studio", host, port):
            console.print(f"[yellow]LM Studio server not available at {host}:{port}[/]")
            console.print("[dim]Start LM Studio and enable API server.[/]")

        _set_local_config("lm_studio", model_name, host, port)
        console.print(f"[green]Switched to LM Studio model: {model_name}[/]")
        console.print("[dim]Restart deeptutor for changes to take effect.[/]")

    @app.command("current")
    def model_current() -> None:
        """Show current model configuration."""
        config = _get_current_config()
        
        table = Table(title="Current Model Configuration")
        table.add_column("Setting", style="bold")
        table.add_column("Value")

        for key, value in config.items():
            table.add_row(key, str(value))

        console.print(table)

    @app.command("info")
    def model_info(
        model_name: str = typer.Argument(..., help="Model name to get info for."),
    ) -> None:
        """Get detailed information about a model."""
        info = _get_model_info(model_name)
        
        if not info:
            console.print(f"[red]Model '{model_name}' not found.[/]")
            raise typer.Exit(code=1)

        console.print_json(json.dumps(info, indent=2, ensure_ascii=False, default=str))


def _get_all_models() -> list[dict]:
    models = []
    
    ollama_models = _get_ollama_models()
    for model in ollama_models:
        models.append({
            "name": model["name"],
            "provider": "ollama",
            "type": "local",
            "status": "available",
        })
    
    return models


def _get_ollama_models(host: str = "localhost", port: int = 11434) -> list[dict]:
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("models", [])
    except requests.exceptions.RequestException:
        pass
    return []


def _check_server(provider: str, host: str, port: int) -> bool:
    try:
        url = f"http://{host}:{port}/v1/models" if provider != "ollama" else f"http://{host}:{port}/api/tags"
        response = requests.get(url, timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _set_local_config(provider: str, model_name: str, host: str, port: int) -> None:
    env_path = Path(".env")
    
    config_lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            config_lines = f.readlines()
    
    new_lines = []
    llm_binding_set = False
    llm_model_set = False
    llm_host_set = False
    llm_api_key_set = False
    
    api_base = f"http://{host}:{port}/v1"
    
    for line in config_lines:
        if line.startswith("LLM_BINDING="):
            new_lines.append(f"LLM_BINDING={provider}\n")
            llm_binding_set = True
        elif line.startswith("LLM_MODEL="):
            new_lines.append(f"LLM_MODEL={model_name}\n")
            llm_model_set = True
        elif line.startswith("LLM_HOST="):
            new_lines.append(f"LLM_HOST={api_base}\n")
            llm_host_set = True
        elif line.startswith("LLM_API_KEY="):
            new_lines.append(f"LLM_API_KEY=\n")
            llm_api_key_set = True
        else:
            new_lines.append(line)
    
    if not llm_binding_set:
        new_lines.append(f"LLM_BINDING={provider}\n")
    if not llm_model_set:
        new_lines.append(f"LLM_MODEL={model_name}\n")
    if not llm_host_set:
        new_lines.append(f"LLM_HOST={api_base}\n")
    if not llm_api_key_set:
        new_lines.append("LLM_API_KEY=\n")
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def _get_current_config() -> dict:
    config = {
        "LLM_BINDING": os.environ.get("LLM_BINDING", "not set"),
        "LLM_MODEL": os.environ.get("LLM_MODEL", "not set"),
        "LLM_HOST": os.environ.get("LLM_HOST", "not set"),
        "LLM_API_KEY": "***" if os.environ.get("LLM_API_KEY") else "(empty)",
        "Ollama Available": "Yes" if _get_ollama_models() else "No",
        "SGLang Available": "Yes" if _check_server("sglang", "localhost", 8000) else "No",
        "vLLM Available": "Yes" if _check_server("vllm", "localhost", 8000) else "No",
        "LM Studio Available": "Yes" if _check_server("lm_studio", "localhost", 1234) else "No",
    }
    return config


def _get_model_info(model_name: str) -> dict | None:
    ollama_models = _get_ollama_models()
    for model in ollama_models:
        if model["name"] == model_name:
            return model
    
    try:
        response = requests.get(f"http://localhost:11434/api/show", params={"name": model_name}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    
    return None