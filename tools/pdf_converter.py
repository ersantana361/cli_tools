import pyperclip
import traceback
from rich.progress import Progress
from docling.document_converter import DocumentConverter

def run_conversion(input_source, output_path, verbose, markdown_format, clipboard, console):
    """
    Main PDF conversion handler with rich feedback and error handling
    
    Args:
        input_source: PDF file path or URL
        output_path: Output markdown file path
        verbose: Show detailed diagnostics
        markdown_format: basic/enhanced formatting
        clipboard: Copy to system clipboard
        console: Rich console instance for output
    """
    try:
        with Progress(console=console, transient=True) as progress:
            task = progress.add_task("[cyan]Processing document...", total=5)
            
            # Initialization phase
            progress.update(task, advance=1, description="[cyan]Initializing converter...")
            converter = DocumentConverter()
            
            # Document loading
            progress.update(task, advance=1, description="[cyan]Loading source...")
            result = converter.convert(input_source)
            
            # Content generation
            progress.update(task, advance=1, description="[cyan]Generating Markdown...")
            markdown_content = result.document.export_to_markdown()
            
            # Formatting stage
            progress.update(task, advance=1, description="[cyan]Formatting output...")
            if markdown_format == "enhanced":
                markdown_content = apply_enhanced_formatting(markdown_content)
            
            # File output
            progress.update(task, advance=1, description="[cyan]Saving file...")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            # Optional clipboard integration
            if clipboard:
                pyperclip.copy(markdown_content)
                console.print("\n📋 Content copied to clipboard!", style="bold green")

        console.print(f"\n✅ Successfully saved to [bold]{output_path}[/]", style="green")
        
        # Verbose diagnostics
        if verbose:
            console.print("\n[bold]Conversion Details:", style="blue")
            console.print(f"- Input type: {'URL' if '://' in input_source else 'File'}", style="cyan")
            console.print(f"- Output format: {markdown_format}", style="cyan")
            console.print(f"- Content length: {len(markdown_content)} characters", style="cyan")

    except Exception as e:
        console.print(f"\n❌ Conversion failed: {e}", style="bold red")
        if verbose:
            console.print("\n[bold]Error Details:", style="yellow")
            traceback.print_exc()

def apply_enhanced_formatting(content):
    """
    Applies additional formatting to the generated markdown
    """
    return f"# Converted Document\n\n{content}\n\n<!-- Converted with Document Converter -->"
