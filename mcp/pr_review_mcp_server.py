#!/usr/bin/env python3
"""
MCP Server for PR Review Tool using FastMCP style
"""

import sys
import io
import contextlib
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp import FastMCP
    except ImportError:
        print("Could not import FastMCP. Please ensure the correct MCP SDK is installed.")
        print("You might need to run: pip install \"mcp[cli]\" or check the specific MCP Python SDK documentation.")
        sys.exit(1)

try:
    from claude_integrated_pr_review import ClaudeIntegratedPRReviewer
    print("Successfully imported ClaudeIntegratedPRReviewer.")
except ImportError as e:
    print(f"Failed to import ClaudeIntegratedPRReviewer: {e}")
    print("Make sure claude_integrated_pr_review.py is in the same directory or your Python path.")
    print("This script will continue with a placeholder if it's not found, but the tool will error.")
    class ClaudeIntegratedPRReviewer:
        def execute_review(self, command: dict) -> bool:
            print(f"Placeholder ClaudeIntegratedPRReviewer: execute_review called with {command}")
            print("Please ensure the real ClaudeIntegratedPRReviewer is available.")
            return False

# Store name and description in variables if you want to print them
server_name_variable = "pr-review-tool-server"
server_description_variable = "A server to review GitHub Pull Requests"
mcp_server = FastMCP(name=server_name_variable, description=server_description_variable)
pr_reviewer_instance = ClaudeIntegratedPRReviewer()

class OutputCapture:
    """Captures stdout and stderr for returning detailed output"""
    
    def __init__(self):
        self.stdout_capture = io.StringIO()
        self.stderr_capture = io.StringIO()
        
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def get_output(self) -> str:
        stdout_content = self.stdout_capture.getvalue()
        stderr_content = self.stderr_capture.getvalue()
        
        output = ""
        if stdout_content:
            output += "📊 **REVIEW OUTPUT:**\n```\n" + stdout_content + "\n```\n\n"
        if stderr_content:
            output += "🔍 **DEBUG INFO:**\n```\n" + stderr_content + "\n```\n\n"
        
        return output

@mcp_server.tool(
    name="review_github_pr",
    description="Reviews a GitHub pull request, providing comprehensive AI-powered analysis. Returns the full review output including analysis, recommendations, and any issues found."
)
def review_pr_tool(
    pr_number: int,
    review_type: str = "categorized",
    dry_run: bool = True,
    repo_name: Optional[str] = None
) -> str:
    """
    Callable tool to review a GitHub PR using the integrated PR reviewer.
    Parameters:
    - pr_number (int): The pull request number.
    - review_type (str): Type of review. Valid options: 'categorized', 'security', 'performance', 'maintainability', 'files', 'summary', 'all'. Default: 'categorized'.
    - dry_run (bool): If True, performs a dry run without posting comments. Default: True.
    - repo_name (str, optional): Repository name in format 'owner/repo'. If not provided, will try to auto-detect.
    """
    print(f"🚀 Starting PR review tool...")
    print(f"   📋 PR Number: {pr_number}")
    print(f"   🔍 Review Type: {review_type}")
    print(f"   🎯 Dry Run: {dry_run}")
    print(f"   📁 Repository: {repo_name or 'Auto-detect'}")
    
    try:
        # Build command for the reviewer
        command = {
            "pr_number": pr_number,
            "review_type": review_type,
            "dry_run": dry_run,
            "confirmed": not dry_run,
            "repo_name": repo_name
        }
        
        print(f"📋 Command prepared: {command}")
        
        # Capture all output from the review process
        with OutputCapture() as capture:
            try:
                success = pr_reviewer_instance.execute_review(command)
            except Exception as e:
                print(f"❌ Exception during review execution: {str(e)}")
                import traceback
                traceback.print_exc()
                success = False
        
        # Get the captured output
        review_output = capture.get_output()
        
        # Build the response
        if success:
            result = f"✅ **PR #{pr_number} Review Completed Successfully**\n\n"
            result += f"**📋 Review Details:**\n"
            result += f"- 🎯 Review Type: {review_type}\n"
            result += f"- 🔍 Mode: {'Dry Run (no comments posted)' if dry_run else 'Live (comments posted)'}\n"
            result += f"- 📁 Repository: {repo_name or 'Auto-detected'}\n\n"
            
            if review_output:
                result += review_output
            else:
                result += "⚠️ No detailed output captured. Check server logs.\n\n"
                
            if dry_run:
                result += f"💡 **Next Steps:** To actually post comments, call again with `dry_run=false`\n"
        else:
            result = f"❌ **PR #{pr_number} Review Failed**\n\n"
            result += f"**📋 Attempted Review:**\n"
            result += f"- 🎯 Review Type: {review_type}\n"
            result += f"- 📁 Repository: {repo_name or 'Auto-detect'}\n\n"
            
            if review_output:
                result += review_output
            else:
                result += "❌ No output captured. Possible issues:\n"
                result += "- GitHub token not configured (GITHUB_TOKEN_WORK, GITHUB_TOKEN, or GITHUB_TOKEN_PERSONAL)\n"
                result += "- LLM API key not set (ANTHROPIC_API_KEY or OPENAI_API_KEY)\n"
                result += "- Repository not found or PR number invalid\n"
                result += "- Network connectivity issues\n\n"
            
            result += "🔍 **Troubleshooting:** Check the server logs for detailed error information.\n"
        
        print(f"🎬 Tool execution completed. Success: {success}")
        return result
        
    except Exception as e:
        error_message = f"💥 **Fatal Error in PR Review Tool**\n\n"
        error_message += f"**Error Details:**\n```\n{str(e)}\n```\n\n"
        error_message += f"**Parameters:**\n"
        error_message += f"- PR Number: {pr_number}\n"
        error_message += f"- Review Type: {review_type}\n"
        error_message += f"- Repository: {repo_name}\n\n"
        
        print(f"💥 Fatal error in review tool: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return error_message

def main():
    print(f"🚀 Starting MCP Server: {server_name_variable}...")
    print(f"📝 Description: {server_description_variable}")
    
    print("\n🔧 Registered tools:")
    # Check if 'tools' attribute exists and is iterable; different SDK versions might vary
    if hasattr(mcp_server, 'tools') and isinstance(mcp_server.tools, dict) and mcp_server.tools:
        for tool_name, tool_impl in mcp_server.tools.items():
            tool_desc = ""
            # Attempt to get description from tool object's 'description' attribute
            if hasattr(tool_impl, 'description') and tool_impl.description:
                tool_desc = tool_impl.description
            # Fallback to the function's docstring
            elif hasattr(tool_impl, 'func') and tool_impl.func.__doc__:
                tool_desc = tool_impl.func.__doc__.strip().split('\n')[0]
            elif tool_impl.__doc__: # If tool_impl itself is the function (older SDKs?)
                 tool_desc = tool_impl.func.__doc__.strip().split('\n')[0]
            print(f"  - 🛠️ {tool_name}: {tool_desc}")
    else:
        # If you know your SDK version stores tool details differently, adjust here
        # For now, just print a generic message if .tools isn't as expected
        print("  (Tool details might be structured differently in this MCP SDK version or no tools registered)")
        print("  🛠️ Tool 'review_github_pr' is registered and should be available to Claude.")

    print(f"\n✅ Server ready! Press Ctrl+C to exit.")
    print(f"🔍 Listening for PR review requests...")
    
    try:
        mcp_server.run()
    except Exception as e:
        print(f"❌ Error during mcp_server.run(): {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎬 MCP Server script starting...")
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down due to KeyboardInterrupt...")
    except Exception as e:
        print(f"💥 FATAL: Error running MCP server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 MCP Server script finished.")
