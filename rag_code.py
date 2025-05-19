import os
import anthropic
import sys # For exiting gracefully
import time

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
import pathspec # For .gitignore parsing (pip install pathspec)

# --- RAG Specific Imports ---
# pip install langchain langchain-community sentence-transformers faiss-cpu tiktoken
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- Initialize Rich Console ---
console = Console()

# --- Configuration ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    console.print("[bold yellow]Anthropic API Key not found in environment variables.[/bold yellow]")
    ANTHROPIC_API_KEY = questionary.password("Please enter your Anthropic API Key:").ask()
    if not ANTHROPIC_API_KEY: # Handle if user cancels or enters empty
        console.print("[bold red]API Key is required to proceed. Exiting.[/bold red]")
        sys.exit(1)


PROJECT_DIRECTORY = os.getcwd()
console.print(Panel(f"Using current working directory as project root:\n[blue]{PROJECT_DIRECTORY}[/blue]", title="[bold green]Project Directory[/bold green]", expand=False))


# Updated file extensions for a Java Gradle project
FILE_EXTENSIONS_TO_SCAN = ['.kt', '.java', '.md', '.yaml', '.kts', '.json', '.yml', '.sh']
MAX_TOKENS_TO_SAMPLE = 4000  # Max tokens for Anthropic API response
MODEL_NAME = "claude-3-opus-20240229" # Or "claude-3-sonnet-20240229", "claude-3-haiku-20240307"

# RAG Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" # A popular, good quality sentence embedding model
CHUNK_SIZE = 1000  # Characters per chunk (tune based on your content and model context preference)
CHUNK_OVERLAP = 150 # Characters of overlap between chunks
VECTOR_STORE_PATH = "project_faiss_index_enhanced" # Directory to save/load the FAISS index

# --- New: Directory and File Exclusion Configuration ---
DEFAULT_EXCLUDE_DIRS = [
    ".git", ".idea", ".vscode", "__pycache__", "node_modules", "venv",
    "build", "target", "dist", "out", ".gradle", "docs_build",
    "site", "*.egg-info", ".DS_Store", "coverage", "logs", "*.log",
    ".pytest_cache", ".mypy_cache", ".tox"
]
# Users could potentially extend this or provide custom patterns in a more advanced version
USER_EXCLUDE_DIRS = [] # Placeholder for future customization
USER_EXCLUDE_PATTERNS = [] # Placeholder for glob patterns


# --- Initialize Anthropic Client ---
console.print(f"\n[INFO] Initializing Anthropic client with model: [cyan]{MODEL_NAME}[/cyan]...")
try:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    console.print("[SUCCESS] Anthropic client initialized.", style="bold green")
except Exception as e:
    console.print(f"[ERROR] Failed to initialize Anthropic client: {e}", style="bold red")
    sys.exit(1)

# --- Initialize Embedding Model ---
console.print(f"\n[INFO] Initializing embedding model: [cyan]{EMBEDDING_MODEL_NAME}[/cyan]...")
console.print("[INFO] This might take a moment if downloading for the first time.")
try:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task("Initializing embeddings...", total=None)
        start_time = time.time()
        embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        end_time = time.time()
    console.print(f"[SUCCESS] Embedding model initialized in {end_time - start_time:.2f} seconds.", style="bold green")
except Exception as e:
    console.print(f"[ERROR] Failed to initialize embedding model: {e}", style="bold red")
    console.print("[INFO] Please ensure 'sentence-transformers' is installed and the model name is correct.")
    sys.exit(1)

def get_gitignore_spec(directory):
    """Loads and parses .gitignore file from the given directory."""
    gitignore_path = os.path.join(directory, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding='utf-8') as f:
                return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
        except Exception as e:
            console.print(f"[WARNING] Could not read or parse .gitignore: {e}", style="yellow")
    return None

def find_files_by_extension(directory, extensions, exclude_dirs, gitignore_spec):
    """
    Recursively finds files with given extensions, excluding specified directories and .gitignored files.
    """
    console.print(Panel("Phase 1/5: Scanning for Files", title="[bold magenta]File Discovery[/bold magenta]", expand=False))
    console.print(f"[INFO] Searching in directory: [blue]{directory}[/blue]")
    console.print(f"[INFO] Looking for extensions: [cyan]{', '.join(extensions)}[/cyan]")
    console.print(f"[INFO] Excluding directories: [yellow]{', '.join(exclude_dirs)}[/yellow]")
    if gitignore_spec:
        console.print("[INFO] Applying .gitignore rules.")

    matched_files = []
    scanned_file_count = 0
    excluded_by_dir_count = 0
    excluded_by_gitignore_count = 0

    # Estimate total items for progress bar
    # This estimation can be slow for very large directory trees.
    # For extremely large projects, consider removing or simplifying this pre-scan.
    items_to_scan_estimate = 0
    try:
        for _, dirnames_est, filenames_est in os.walk(directory, topdown=True):
            dirnames_est[:] = [d for d in dirnames_est if d not in exclude_dirs and not d.startswith('.')]
            items_to_scan_estimate += len(filenames_est)
    except Exception as e:
        console.print(f"[WARNING] Could not accurately estimate total files for progress: {e}", style="yellow")
        items_to_scan_estimate = None # Indeterminate progress

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress_bar:
        scan_task = progress_bar.add_task("Scanning directories...", total=items_to_scan_estimate)

        for root, dirs, files in os.walk(directory, topdown=True):
            original_dir_count = len(dirs)
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')] # Exclude hidden too
            excluded_by_dir_count += (original_dir_count - len(dirs))

            for file in files:
                scanned_file_count += 1
                progress_bar.update(scan_task, advance=1, description=f"Scanning: {os.path.join(root,file)[-60:]}") # Show tail

                file_path_full = os.path.join(root, file)
                try:
                    file_path_relative_to_project_root = os.path.relpath(file_path_full, directory)
                except ValueError: # Handle if file is not under directory (e.g. symlink pointing outside)
                    file_path_relative_to_project_root = file_path_full


                if gitignore_spec and gitignore_spec.match_file(file_path_relative_to_project_root):
                    excluded_by_gitignore_count +=1
                    continue

                if any(file.endswith(ext) for ext in extensions):
                    matched_files.append(file_path_full)
            if items_to_scan_estimate is None: # Update total if it was indeterminate
                progress_bar.update(scan_task, total=scanned_file_count + 100) # Add some buffer

    console.print(f"[INFO] Scanned {scanned_file_count} total files/items in the directory tree.")
    if excluded_by_dir_count > 0:
        console.print(f"[INFO] Excluded {excluded_by_dir_count} items due to directory exclusion rules.", style="yellow")
    if excluded_by_gitignore_count > 0:
        console.print(f"[INFO] Excluded {excluded_by_gitignore_count} items due to .gitignore rules.", style="yellow")

    if matched_files:
        console.print(f"[SUCCESS] Found {len(matched_files)} files matching criteria.", style="bold green")
    else:
        console.print(f"[WARNING] No files found matching criteria in {directory}.", style="bold yellow")
    return matched_files


def load_and_chunk_files(file_paths):
    console.print(Panel("Phase 2/5: Loading and Chunking Files", title="[bold magenta]Document Processing[/bold magenta]", expand=False))
    documents = []
    if not file_paths:
        console.print("[INFO] No files to load and chunk.")
        return []

    loaded_count = 0
    skipped_files = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description} ({task.completed}/{task.total})"), BarColumn(), TimeElapsedColumn(), console=console, transient=False) as progress:
        task = progress.add_task(f"Loading {len(file_paths)} files...", total=len(file_paths))
        for i, file_path in enumerate(file_paths):
            progress.update(task, advance=1, description=f"Loading: {os.path.basename(file_path)}")
            try:
                loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
                loaded_docs_for_file = loader.load()
                for doc in loaded_docs_for_file:
                    doc.metadata["source"] = file_path
                documents.extend(loaded_docs_for_file)
                loaded_count +=1
            except Exception as e:
                skipped_files.append(f"{file_path} (Reason: {str(e)[:100]})") # Limit reason length
                continue
    console.print(f"[INFO] Successfully loaded content from {loaded_count}/{len(file_paths)} files.")
    if skipped_files:
        console.print(f"[WARNING] Skipped {len(skipped_files)} files due to errors:", style="yellow")
        for sf_idx, sf in enumerate(skipped_files):
            if sf_idx < 5: # Print first 5 skipped
                console.print(f"  - {sf}", style="yellow")
        if len(skipped_files) > 5:
            console.print(f"  ...and {len(skipped_files)-5} more.", style="yellow")


    if not documents:
        console.print("[WARNING] No documents were successfully loaded for chunking.", style="bold yellow")
        return []

    console.print(f"[INFO] Chunking {len(documents)} loaded document sections...")
    console.print(f"[INFO] Chunk size: {CHUNK_SIZE} chars, Overlap: {CHUNK_OVERLAP} chars.")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    chunked_documents = []
    # Simpler progress for chunking as it's often a single quick operation on in-memory data
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
        progress.add_task("Chunking documents...", total=None)
        start_time = time.time()
        chunked_documents = text_splitter.split_documents(documents)
        end_time = time.time()

    if chunked_documents:
        console.print(f"[SUCCESS] Chunked documents into {len(chunked_documents)} chunks in {end_time - start_time:.2f} seconds.", style="bold green")
    else:
        console.print("[WARNING] No chunks were created. This might be due to empty files or very small content.", style="bold yellow")
    return chunked_documents

def create_or_load_vector_store(chunks, embeddings, store_path):
    console.print(Panel("Phase 3/5: Vector Store Management", title="[bold magenta]Data Indexing[/bold magenta]", expand=False))
    if os.path.exists(store_path):
        try:
            console.print(f"[INFO] Attempting to load existing vector store from: [blue]{store_path}[/blue]")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
                progress.add_task(f"Loading FAISS index from {store_path}...", total=None)
                start_time = time.time()
                vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
                end_time = time.time()
            console.print(f"[SUCCESS] Existing vector store loaded in {end_time - start_time:.2f} seconds.", style="bold green")
            return vector_store
        except Exception as e:
            console.print(f"[WARNING] Error loading vector store from {store_path}: {e}. Will attempt to rebuild.", style="yellow")

    if not chunks:
        console.print("[ERROR] No chunks available to create a new vector store.", style="bold red")
        return None

    console.print(f"[INFO] Creating new vector store with {len(chunks)} chunks. This may take some time...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), console=console, transient=False) as progress:
        # FAISS.from_documents is a single operation, hard to track sub-steps without modifying Langchain
        # So we show a spinner for the overall operation and then mark it complete.
        # The 'total' for the progress bar here is more symbolic.
        task = progress.add_task("Building FAISS index...", total=1)
        start_time = time.time()
        try:
            vector_store = FAISS.from_documents(chunks, embeddings)
            progress.update(task, completed=1) # Mark as complete
            vector_store.save_local(store_path)
            end_time = time.time()
            console.print(f"[SUCCESS] New vector store created and saved to [blue]{store_path}[/blue] in {end_time - start_time:.2f} seconds.", style="bold green")
            return vector_store
        except Exception as e:
            console.print(f"[ERROR] Failed to create new vector store: {e}", style="bold red")
            progress.update(task, description=f"[bold red]Failed: {e}[/bold red]")
            return None


def retrieve_relevant_context(query, vector_store, top_k=5):
    console.print(Panel("Phase 4/5: Retrieving Context", title="[bold magenta]Information Retrieval[/bold magenta]", expand=False))
    console.print(f"[INFO] Query: '[italic]{query}[/italic]'")
    console.print(f"[INFO] Retrieving top {top_k} relevant chunks from vector store.")

    if not vector_store:
        console.print("[ERROR] Vector store is not available for retrieval.", style="bold red")
        return "", [], [] # Added empty list for docs_info

    context_str = ""
    sources = []
    retrieved_docs_info = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
        progress.add_task("Searching vector store...", total=None)
        start_time = time.time()
        try:
            # Using similarity_search_with_score to get scores
            retrieved_docs_with_scores = vector_store.similarity_search_with_score(query, k=top_k)
            end_time = time.time()
        except Exception as e:
            console.print(f"[ERROR] Error during similarity search: {e}", style="bold red")
            return "", [], []

    if not retrieved_docs_with_scores:
        console.print("[WARNING] No relevant chunks found in the vector store for this query.", style="yellow")
        return "", [], []

    console.print(f"[SUCCESS] Retrieved {len(retrieved_docs_with_scores)} chunks in {end_time - start_time:.2f} seconds.", style="bold green")

    table = Table(title="Retrieved Chunks", show_lines=True, expand=False)
    table.add_column("No.", style="dim", width=3, justify="right")
    table.add_column("Source File", style="blue", overflow="fold", min_width=20, max_width=60)
    table.add_column("Score", style="magenta", justify="center") # FAISS L2 distance: lower is better.

    console.print("[INFO] Assembling context from retrieved chunks:")
    for i, (doc, score) in enumerate(retrieved_docs_with_scores):
        source_file = doc.metadata.get('source', 'Unknown source')
        relative_source_file = os.path.relpath(source_file, PROJECT_DIRECTORY) if os.path.isabs(source_file) and source_file.startswith(PROJECT_DIRECTORY) else source_file

        retrieved_docs_info.append({
            "id": i + 1,
            "source": relative_source_file,
            "score": f"{score:.4f}",
            "content_preview": doc.page_content[:150].replace("\n", " ") + "..."
        })
        table.add_row(str(i+1), relative_source_file, f"{score:.4f}")

        context_str += f"--- Relevant Chunk {i+1} from {relative_source_file} (Score: {score:.4f}) ---\n"
        context_str += doc.page_content
        context_str += "\n\n"
        sources.append(source_file)

    console.print(table)
    return context_str.strip(), list(set(sources)), retrieved_docs_info


def query_anthropic_with_rag(user_query, context, sources_metadata, analysis_type="vulnerabilities"):
    console.print(Panel("Phase 5/5: Querying Anthropic API", title="[bold magenta]AI Analysis[/bold magenta]", expand=False))
    console.print(f"[INFO] Analysis type: [cyan]{analysis_type}[/cyan]")

    if not context:
        console.print("[WARNING] No context was retrieved. Sending query to Anthropic without specific file context.", style="yellow")
        context = "No specific relevant code snippets were retrieved from the project files for this query."
        source_files_display = ["N/A (no context retrieved)"]
    else:
        relative_sources = sorted(list(set(os.path.relpath(s, PROJECT_DIRECTORY) if os.path.isabs(s) and s.startswith(PROJECT_DIRECTORY) else s for s in sources_metadata)))
        source_files_display = relative_sources


    base_prompt = f"""
Human: You are an expert AI assistant. I am querying my codebase.
My specific query is: "{user_query}"

Based *only* on the following relevant code snippets extracted from my project files (if any were found), please perform the requested analysis.
If the provided context is empty or does not contain information relevant to the query or shows no clear issues/areas for improvement based on the query, please state that clearly. Do not invent information beyond the provided context.
For any findings, please reference the source file(s) if mentioned in the chunk metadata.

Relevant Code Snippets:
{context}

Source files of these snippets (for reference): {', '.join(source_files_display)}
"""

    if analysis_type == "vulnerabilities":
        analysis_specific_instructions = """
Please analyze for potential security vulnerabilities related to my query.
Be specific about the type of vulnerability, identify the potentially vulnerable code snippet from the provided context, mention the source file if possible, and suggest a possible mitigation.
"""
    elif analysis_type == "improvements":
        analysis_specific_instructions = """
Please analyze for potential code improvements related to my query (e.g., performance, readability, maintainability, adherence to best practices).
For each suggestion, explain the reasoning and provide an example of how the code could be improved, referencing the provided snippets. Mention the source file if possible.
"""
    else:
        analysis_specific_instructions = "Please provide a general analysis based on the query."

    prompt_to_send = f"{base_prompt}\n{analysis_specific_instructions}\nAssistant:"

    console.print(f"[INFO] Sending request to Anthropic API. Max tokens for response: {MAX_TOKENS_TO_SAMPLE}.")

    error_msg = "" # Initialize error_msg
    with Live(Spinner("dots", style="magenta", text="Contacting Anthropic API..."), console=console, transient=True, refresh_per_second=10) as live:
        start_time = time.time()
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS_TO_SAMPLE,
                messages=[
                    {"role": "user", "content": prompt_to_send.strip()}
                ]
            )
            end_time = time.time()
            # CORRECTED LINE: Style embedded in string
            live.update(f"[bold green][SUCCESS] Received response from Anthropic API in {end_time - start_time:.2f} seconds.[/bold green]")
            time.sleep(0.5) # Keep success message for a bit

            if response.content and isinstance(response.content, list) and hasattr(response.content[0], 'text'):
                return response.content[0].text
            else:
                console.print("[WARNING] No text content found in the API response or unexpected response format.", style="yellow")
                return "No text content found in the API response or unexpected response format."

        except anthropic.APIConnectionError as e:
            error_msg = f"Anthropic API connection error: {e}"
        except anthropic.RateLimitError as e:
            error_msg = f"Anthropic API rate limit exceeded: {e}"
        except anthropic.AuthenticationError as e:
            error_msg = f"Anthropic API authentication error: {e}. Please check your API key."
        except anthropic.APIStatusError as e:
            error_msg = f"Anthropic API status error (status code {e.status_code}): {e.response}"
        except Exception as e:
            error_msg = f"An unexpected error occurred during API call: {e}"

        if error_msg: # If an error message was set
            # CORRECTED LINE: Style embedded in string
            live.update(f"[bold red][ERROR] {error_msg}[/bold red]")
            time.sleep(2) # Keep error message visible
            return f"Error from API: {error_msg}"
        # Fallback if no specific error_msg but didn't return content (should be rare now)
        return "An unknown issue occurred with the API call after attempting."


def main_rag():
    current_time_str = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    console.print(Panel(f"RAG Code Analysis Script - Enhanced UI\n[dim]Current Time: {current_time_str}[/dim]", title="[bold blue]Welcome![/bold blue]", expand=False ))


    if not os.path.isdir(PROJECT_DIRECTORY):
        console.print(f"[ERROR] Project directory '{PROJECT_DIRECTORY}' (current working directory) is not valid.", style="bold red")
        sys.exit(1)

    gitignore_spec = get_gitignore_spec(PROJECT_DIRECTORY)

    all_exclude_dirs = DEFAULT_EXCLUDE_DIRS + USER_EXCLUDE_DIRS
    project_files = find_files_by_extension(PROJECT_DIRECTORY, FILE_EXTENSIONS_TO_SCAN, all_exclude_dirs, gitignore_spec)
    if not project_files:
        console.print("[INFO] No files found to process. Exiting script.")
        return

    chunked_docs = load_and_chunk_files(project_files)
    if not chunked_docs:
        console.print("[INFO] No document chunks were created. Cannot proceed with RAG. Exiting script.")
        return

    vector_store = create_or_load_vector_store(chunked_docs, embeddings_model, VECTOR_STORE_PATH)
    if not vector_store:
        console.print("[ERROR] Failed to initialize vector store. Cannot proceed with RAG. Exiting script.", style="bold red")
        return

    console.print("\n--- [bold green]RAG System Initialized Successfully[/bold green] ---")
    console.print("You can now ask questions about your codebase.")

    while True:
        console.rule("[bold cyan]New Query[/bold cyan]")
        user_query_input = questionary.text(
            "Enter your query for the codebase (or type 'quit' to exit):",
            validate=lambda text: True if len(text.strip()) > 0 else "Query cannot be empty."
        ).ask()

        if user_query_input is None: # User pressed Ctrl+C or Esc
            console.print("[INFO] Query input cancelled. Exiting RAG query loop. Goodbye!", style="bold yellow")
            break
        
        user_query = user_query_input.strip()
        if user_query.lower() == 'quit':
            console.print("[INFO] Exiting RAG query loop. Goodbye!", style="bold yellow")
            break
        
        analysis_choice = questionary.select(
            "What is the goal of this query?",
            choices=[
                questionary.Choice("Identify potential security vulnerabilities", value="vulnerabilities"),
                questionary.Choice("Suggest code improvements (performance, readability, etc.)", value="improvements"),
            ],
            default="vulnerabilities" # Default choice pre-selected
        ).ask()

        if analysis_choice is None: # User pressed Ctrl+C or Esc
            console.print("[INFO] Analysis type selection cancelled. Please enter a new query or type 'quit'.", style="yellow")
            continue

        context, sources, retrieved_docs_info = retrieve_relevant_context(user_query, vector_store)

        llm_response = query_anthropic_with_rag(user_query, context, sources, analysis_choice)

        console.print(Panel(Markdown(llm_response, code_theme="monokai"), title="[bold green]Anthropic RAG Response[/bold green]", border_style="green", expand=False)) # Set expand to False for potentially long responses
        console.rule("[bold cyan]End of Response[/bold cyan]")

if __name__ == "__main__":
    try:
        main_rag()
    except (KeyboardInterrupt):
        console.print("\n[INFO] Script interrupted by user. Exiting.", style="bold yellow")
    except Exception as e:
        console.print(f"\n[CRITICAL] An unexpected critical error occurred.", style="bold red")
        # Rich traceback for better debugging
        console.print_exception(show_locals=False, width=console.width) # Set show_locals=True for more debug info
    finally:
        console.print("\n[INFO] Script finished.", style="dim")
