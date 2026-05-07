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
    ) -> None:
        """Switch to use a local Ollama model."""
        models = _get_ollama_models()
        model_names = [m["name"] for m in models]
        
        if model_name not in model_names:
            console.print(f"[red]Model '{model_name}' not found in Ollama.[/]")
            console.print(f"[dim]Available models: {', '.join(model_names)}[/]")
            raise typer.Exit(code=1)

        _set_ollama_config(model_name)
        console.print(f"[green]Switched to Ollama model: {model_name}[/]")
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


def _get_ollama_models() -> list[dict]:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("models", [])
    except requests.exceptions.RequestException:
        pass
    return []


def _set_ollama_config(model_name: str) -> None:
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
    
    for line in config_lines:
        if line.startswith("LLM_BINDING="):
            new_lines.append(f"LLM_BINDING=ollama\n")
            llm_binding_set = True
        elif line.startswith("LLM_MODEL="):
            new_lines.append(f"LLM_MODEL={model_name}\n")
            llm_model_set = True
        elif line.startswith("LLM_HOST="):
            new_lines.append(f"LLM_HOST=http://localhost:11434/v1\n")
            llm_host_set = True
        elif line.startswith("LLM_API_KEY="):
            new_lines.append(f"LLM_API_KEY=\n")
            llm_api_key_set = True
        else:
            new_lines.append(line)
    
    if not llm_binding_set:
        new_lines.append("LLM_BINDING=ollama\n")
    if not llm_model_set:
        new_lines.append(f"LLM_MODEL={model_name}\n")
    if not llm_host_set:
        new_lines.append("LLM_HOST=http://localhost:11434/v1\n")
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