"""Configuration for the ComfyUI FL-MCP bridge."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    backend_launch_mode: Literal["auto", "terminal", "subprocess", "manual"] = "subprocess"
    auto_start_backend: bool = True
    auto_restart_backend: bool = True
    log_backend_to_file: bool = True

    ws_host: str = "127.0.0.1"
    ws_port: int = 8000
    ws_heartbeat_interval: int = 30
    ws_session_timeout: int = 300
    ws_max_reconnect_attempts: int = 5

    max_connections_per_ip: int = 10
    max_message_size: int = 1000000
    tool_timeout: int = 30000
    max_tool_retries: int = 3

    comfyui_server_url: str = "http://127.0.0.1:8188"
    comfyui_api_timeout: int = 10
    public_url: str = "http://127.0.0.1:8000"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "text"

    enable_workflow_writes: bool = Field(False, validation_alias="FL_MCP_ENABLE_WORKFLOW_WRITES")
    enable_custom_node_writes: bool = Field(False, validation_alias="FL_MCP_ENABLE_CUSTOM_NODE_WRITES")
    enable_git_writes: bool = Field(False, validation_alias="FL_MCP_ENABLE_GIT_WRITES")
    enable_manager_mutations: bool = Field(False, validation_alias="FL_MCP_ENABLE_MANAGER_MUTATIONS")
    enable_comfy_process_control: bool = Field(False, validation_alias="FL_MCP_ENABLE_COMFY_PROCESS_CONTROL")


settings = Settings()
