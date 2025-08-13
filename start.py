# app/start.py
"""
DocuReview Pro - Application Startup Script
Easy startup with environment validation and initialization
"""
import os
import sys
import uvicorn
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database import init_database

console = Console()

def validate_environment() -> bool:
    """
    Validate environment configuration and dependencies
    
    Returns:
        bool: True if environment is valid
    """
    console.print("\n🔍 [bold blue]Validating Environment...[/bold blue]")
    
    issues = []
    warnings = []
    
    # Check required environment variables
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": Config.AZURE_OPENAI_ENDPOINT,
        "AZURE_OPENAI_API_KEY": Config.AZURE_OPENAI_API_KEY,
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            issues.append(f"Missing required environment variable: {var_name}")
    
    # Check optional but recommended variables
    optional_vars = {
        "SENTENCE_TRANSFORMER_MODEL": Config.SENTENCE_TRANSFORMER_MODEL,
        "CHUNK_SIZE": Config.CHUNK_SIZE,
        "UPLOAD_FOLDER": Config.UPLOAD_FOLDER,
    }
    
    for var_name, var_value in optional_vars.items():
        if not var_value:
            warnings.append(f"Using default for {var_name}: {getattr(Config, var_name.split('_')[-1], 'N/A')}")
    
    # Check directory permissions
    try:
        upload_dir = Path(Config.UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = upload_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
    except Exception as e:
        issues.append(f"Upload directory not writable: {Config.UPLOAD_FOLDER} - {e}")
    
    # Check database path
    try:
        db_path = Path(Config.DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        issues.append(f"Database directory not accessible: {db_path.parent} - {e}")
    
    # Check Python dependencies
    missing_deps = []
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "openai", 
        "sentence_transformers", "faiss", "numpy", "pydantic"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_deps.append(package)
    
    if missing_deps:
        issues.append(f"Missing Python packages: {', '.join(missing_deps)}")
        issues.append("Run: pip install -r requirements.txt")
    
    # Display results
    if issues:
        console.print("\n❌ [bold red]Environment Issues Found:[/bold red]")
        for issue in issues:
            console.print(f"  • {issue}")
        return False
    
    if warnings:
        console.print("\n⚠️ [bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")
    
    console.print("✅ [bold green]Environment validation passed![/bold green]")
    return True

def initialize_application() -> bool:
    """
    Initialize application database and services
    
    Returns:
        bool: True if initialization successful
    """
    console.print("\n🚀 [bold blue]Initializing Application...[/bold blue]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize database
            task1 = progress.add_task("Initializing database...", total=None)
            init_database()
            progress.update(task1, completed=100)
            
            # Validate configuration
            task2 = progress.add_task("Validating configuration...", total=None)
            Config.validate_config()
            progress.update(task2, completed=100)
            
            # Create upload directories
            task3 = progress.add_task("Creating directories...", total=None)
            Config.ensure_upload_folder()
            progress.update(task3, completed=100)
            
            # Test AI services (optional)
            if Config.AZURE_OPENAI_API_KEY:
                task4 = progress.add_task("Testing AI services...", total=None)
                try:
                    from services.llm_service import LLMService
                    llm_service = LLMService(
                        endpoint=Config.AZURE_OPENAI_ENDPOINT,
                        api_key=Config.AZURE_OPENAI_API_KEY,
                        api_version=Config.AZURE_OPENAI_API_VERSION,
                        deployment=Config.AZURE_OPENAI_DEPLOYMENT
                    )
                    progress.update(task4, completed=100)
                except Exception as e:
                    console.print(f"⚠️ AI service test failed: {e}")
        
        console.print("✅ [bold green]Application initialized successfully![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"❌ [bold red]Initialization failed: {e}[/bold red]")
        return False

def display_startup_info():
    """Display application startup information"""
    
    # Application info table
    info_table = Table(title="DocuReview Pro - Configuration")
    info_table.add_column("Setting", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="magenta")
    
    info_table.add_row("Application", f"{Config.APP_NAME} v{Config.APP_VERSION}")
    info_table.add_row("Host", Config.HOST)
    info_table.add_row("Port", str(Config.PORT))
    info_table.add_row("Debug Mode", "Yes" if Config.DEBUG else "No")
    info_table.add_row("Database", str(Config.get_database_path()))
    info_table.add_row("Upload Folder", str(Config.ensure_upload_folder()))
    info_table.add_row("Chunk Size", str(Config.CHUNK_SIZE))
    info_table.add_row("AI Model", Config.AZURE_OPENAI_DEPLOYMENT)
    
    console.print(info_table)
    
    # URLs panel
    urls = [
        f"🌐 Web Interface: http://{Config.HOST}:{Config.PORT}",
        f"📖 API Documentation: http://{Config.HOST}:{Config.PORT}/api/docs",
        f"🔧 Admin Panel: http://{Config.HOST}:{Config.PORT}/admin",
    ]
    
    console.print(Panel(
        "\n".join(urls),
        title="🚀 Access URLs",
        border_style="green"
    ))

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description="DocuReview Pro - Document Analysis Platform")
    parser.add_argument("--host", default=Config.HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=Config.PORT, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--skip-validation", action="store_true", help="Skip environment validation")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args()
    
    # Display banner
    console.print(Panel(
        f"""
[bold cyan]DocuReview Pro[/bold cyan]
[blue]Enterprise Document Version Management & Analysis[/blue]

Version: {Config.APP_VERSION}
Python: {sys.version.split()[0]}
        """.strip(),
        border_style="blue"
    ))
    
    # Environment validation
    if not args.skip_validation:
        if not validate_environment():
            console.print("\n❌ [bold red]Environment validation failed. Use --skip-validation to bypass.[/bold red]")
            sys.exit(1)
    
    # Application initialization
    if not initialize_application():
        console.print("\n❌ [bold red]Application initialization failed.[/bold red]")
        sys.exit(1)
    
    # Update config from args
    if args.debug:
        Config.DEBUG = True
    
    # Display startup information
    display_startup_info()
    
    # Start server
    console.print(f"\n🎯 [bold green]Starting server...[/bold green]")
    
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload or Config.DEBUG,
            workers=args.workers if not (args.reload or Config.DEBUG) else 1,
            log_level=args.log_level,
            access_log=True,
            loop="auto"
        )
    except KeyboardInterrupt:
        console.print("\n👋 [bold yellow]Shutting down gracefully...[/bold yellow]")
    except Exception as e:
        console.print(f"\n❌ [bold red]Server error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()