"""
LLM-based code analysis for PR reviews.
"""

import os
import re
import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from .models import ReviewComment

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM-based code analysis"""
    
    def __init__(self, provider: str = "anthropic"):
        logger.info(f"🧠 Initializing LLM analyzer with provider: {provider}")
        self.provider = provider
        try:
            self.llm = self._initialize_llm()
            logger.info(f"✅ LLM initialized successfully")
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        logger.debug(f"🔧 Setting up {self.provider} LLM...")
        
        if self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                error_msg = "ANTHROPIC_API_KEY environment variable not set"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.debug(f"✅ Anthropic API key found (ends with: ...{api_key[-4:]})")
            
            try:
                llm = ChatAnthropic(
                    api_key=api_key,
                    model="claude-opus-4-20250514"
                )
                logger.info("✅ Claude LLM initialized")
                return llm
            except Exception as e:
                logger.error(f"❌ Failed to initialize Claude: {e}")
                raise
                
        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                error_msg = "OPENAI_API_KEY environment variable not set"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.debug(f"✅ OpenAI API key found (ends with: ...{api_key[-4:]})")
            
            try:
                llm = ChatOpenAI(
                    api_key=api_key,
                    model="gpt-4o"
                )
                logger.info("✅ GPT LLM initialized")
                return llm
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
                raise
        else:
            error_msg = f"Unsupported LLM provider: {self.provider}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def analyze_pr_diff(self, diff: str, pr_info: dict, review_type: str) -> str:
        """Analyze PR diff with LLM"""
        logger.info(f"🤖 Starting AI analysis...")
        logger.info(f"   📋 Review type: {review_type}")
        logger.info(f"   📄 Diff length: {len(diff)} characters")
        logger.info(f"   🏷️  PR title: {pr_info.get('title', 'N/A')}")
        
        try:
            prompt = self._build_analysis_prompt(diff, pr_info, review_type)
            logger.debug(f"📝 Generated prompt ({len(prompt)} characters)")
            logger.debug(f"📝 Prompt preview: {prompt[:300]}...")
            
            logger.info("🚀 Sending request to LLM...")
            response = self.llm.invoke(prompt)
            
            analysis = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ LLM analysis completed ({len(analysis)} characters)")
            logger.debug(f"📄 Analysis preview: {analysis[:200]}...")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Provider: {self.provider}")
            logger.error(f"   Review type: {review_type}")
            return error_msg
    
    def generate_actionable_comments(self, diff: str, pr_info: dict, files: List[dict], review_type: str) -> List[ReviewComment]:
        """Generate actionable review comments with GitHub suggestion support"""
        logger.info("🔨 Generating actionable review comments with suggestions...")
        
        comments = []
        
        try:
            # Build a more targeted prompt for generating specific comments with suggestions
            prompt = self._build_comment_generation_prompt(diff, pr_info, files, review_type)
            logger.debug(f"📝 Generated comment prompt ({len(prompt)} characters)")
            
            logger.info("🚀 Sending comment generation request to LLM...")
            response = self.llm.invoke(prompt)
            
            analysis = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Comment analysis completed ({len(analysis)} characters)")
            
            # Parse the analysis to extract actionable comments with suggestions
            comments = self._parse_analysis_to_comments(analysis, files)
            logger.info(f"✅ Generated {len(comments)} actionable comments")
            
            # Count suggestions for logging
            suggestions_count = sum(1 for comment in comments if comment.has_suggestion())
            if suggestions_count > 0:
                logger.info(f"✨ {suggestions_count} comments include code suggestions")
            
            return comments
            
        except Exception as e:
            logger.error(f"❌ Failed to generate actionable comments: {e}")
            return []
    
    def _build_comment_generation_prompt(self, diff: str, pr_info: dict, files: List[dict], review_type: str) -> str:
        """Build prompt specifically for generating actionable comments with GitHub suggestions"""
        logger.debug(f"🔨 Building comment generation prompt for {review_type}...")
        
        files_summary = "\n".join([f"- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})" for f in files[:10]])
        
        base_prompt = f"""
You are an expert code reviewer. Analyze this pull request and generate specific, actionable review comments with GitHub suggestion blocks where appropriate.

**PR Info:**
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info.get('author', 'N/A')}
- Files changed: {pr_info.get('files_changed', 0)}

**Changed Files:**
{files_summary}

**Full Diff:**
```
{diff}
```

Please provide specific review comments in this EXACT format:

For comments WITHOUT code suggestions:
FILE: filename.ext
LINE: 42
SEVERITY: warning|error|info
COMMENT: Your specific actionable feedback here

For comments WITH code suggestions:
FILE: filename.ext
LINE: 42
SEVERITY: warning|error|info
COMMENT: Brief explanation of the issue or improvement
ORIGINAL_CODE:
original code to be replaced (exact text from the file)
SUGGESTED_CODE:
improved/corrected code that should replace the original
END_LINE: 45 (only if suggestion spans multiple lines)

**GitHub Suggestion Guidelines:**
- Only provide suggestions when you can improve specific code (fix bugs, optimize, enhance readability)
- Extract the EXACT original code from the diff - match it precisely
- Provide clean, working suggested code
- For single-line changes, only specify LINE
- For multi-line changes, specify both LINE and END_LINE
- Make suggestions actionable and clearly better than the original

"""
        
        if review_type == "security":
            prompt = base_prompt + """
Focus on security issues with actionable suggestions:
- SQL injection, XSS, authentication bypasses → provide secure code alternatives
- Hardcoded secrets, unsafe input handling → suggest proper implementations
- Authorization issues and data validation → offer corrected code
- Provide code suggestions to fix security vulnerabilities when possible

Generate 2-5 specific security-focused comments, prioritizing suggestions that fix vulnerabilities.
"""
        elif review_type == "performance":
            prompt = base_prompt + """
Focus on performance issues with optimization suggestions:
- Inefficient algorithms, database queries, loops → provide optimized versions
- Memory leaks, resource management → suggest proper implementations
- Unnecessary computations, network calls → offer efficient alternatives
- Provide code suggestions to improve performance when possible

Generate 2-5 specific performance-focused comments, prioritizing suggestions that optimize code.
"""
        elif review_type == "maintainability":
            prompt = base_prompt + """
Focus on code maintainability with refactoring suggestions:
- Code organization, naming conventions → suggest improvements
- Code duplication, complex functions → provide cleaner alternatives
- Documentation, error handling → offer better implementations
- Provide code suggestions to improve readability and maintainability

Generate 2-5 specific maintainability-focused comments, prioritizing suggestions that clean up code.
"""
        else:  # categorized or other
            prompt = base_prompt + """
Provide a comprehensive review with actionable suggestions covering:
1. **Security** - Fix security concerns with suggested secure alternatives
2. **Performance** - Optimize slow code with efficient implementations  
3. **Code Quality** - Improve maintainability with cleaner code suggestions
4. **Logic** - Correct implementation issues with working alternatives
5. **Testing** - Suggest specific test improvements or missing tests

Generate 3-8 specific comments covering different aspects. Prioritize comments with code suggestions that clearly improve the codebase.
"""
        
        return prompt + "\n\nIMPORTANT: Only comment on files that actually exist in the diff. Use the EXACT format shown above. When providing ORIGINAL_CODE, extract it precisely from the diff - it must match exactly for GitHub suggestions to work."
    
    def _parse_analysis_to_comments(self, analysis: str, files: List[dict]) -> List[ReviewComment]:
        """Parse LLM analysis into structured review comments with suggestion support"""
        logger.debug("🔍 Parsing analysis into structured comments with suggestions...")
        
        comments = []
        file_names = [f['filename'] for f in files]
        
        # Split analysis into sections and look for the structured format
        lines = analysis.split('\n')
        current_comment = {}
        capturing_original = False
        capturing_suggested = False
        original_lines = []
        suggested_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            if stripped_line.startswith('FILE:'):
                # Save previous comment if complete
                if current_comment and self._is_comment_complete(current_comment):
                    comment = self._create_review_comment(current_comment, original_lines, suggested_lines)
                    if comment:
                        comments.append(comment)
                
                # Reset for new comment
                current_comment = {}
                original_lines = []
                suggested_lines = []
                capturing_original = False
                capturing_suggested = False
                
                # Start new comment
                filename = stripped_line.replace('FILE:', '').strip()
                # Validate file exists in the PR
                if filename in file_names:
                    current_comment = {'file': filename}
                else:
                    logger.debug(f"⚠️ Skipping invalid file: {filename}")
                    current_comment = {}  # Skip invalid files
                    
            elif stripped_line.startswith('LINE:') and current_comment:
                try:
                    line_num = int(stripped_line.replace('LINE:', '').strip())
                    current_comment['line'] = line_num
                except ValueError:
                    current_comment['line'] = 1  # Default to line 1 if parsing fails
                    
            elif stripped_line.startswith('END_LINE:') and current_comment:
                try:
                    end_line_num = int(stripped_line.replace('END_LINE:', '').strip())
                    current_comment['end_line'] = end_line_num
                except ValueError:
                    logger.debug("⚠️ Failed to parse END_LINE")
                    
            elif stripped_line.startswith('SEVERITY:') and current_comment:
                severity = stripped_line.replace('SEVERITY:', '').strip().lower()
                if severity in ['warning', 'error', 'info']:
                    current_comment['severity'] = severity
                    
            elif stripped_line.startswith('COMMENT:') and current_comment:
                comment_text = stripped_line.replace('COMMENT:', '').strip()
                current_comment['comment'] = comment_text
                
            elif stripped_line.startswith('ORIGINAL_CODE:') and current_comment:
                capturing_original = True
                capturing_suggested = False
                original_lines = []
                
            elif stripped_line.startswith('SUGGESTED_CODE:') and current_comment:
                capturing_original = False
                capturing_suggested = True
                suggested_lines = []
                
            elif capturing_original:
                # Stop capturing if we hit another keyword or empty line pattern
                if (stripped_line.startswith(('FILE:', 'LINE:', 'SEVERITY:', 'COMMENT:', 'SUGGESTED_CODE:', 'END_LINE:')) or 
                    (not stripped_line and len(original_lines) > 0)):
                    capturing_original = False
                    # Re-process this line since it's not part of original code
                    continue
                else:
                    original_lines.append(line)  # Keep original indentation
                    
            elif capturing_suggested:
                # Stop capturing if we hit another keyword or empty line pattern
                if (stripped_line.startswith(('FILE:', 'LINE:', 'SEVERITY:', 'COMMENT:', 'ORIGINAL_CODE:', 'END_LINE:')) or 
                    (not stripped_line and len(suggested_lines) > 0)):
                    capturing_suggested = False
                    # Re-process this line since it's not part of suggested code
                    continue
                else:
                    suggested_lines.append(line)  # Keep original indentation
        
        # Don't forget the last comment
        if current_comment and self._is_comment_complete(current_comment):
            comment = self._create_review_comment(current_comment, original_lines, suggested_lines)
            if comment:
                comments.append(comment)
        
        # If structured parsing didn't work well, fall back to extracting insights
        if len(comments) < 2:
            logger.warning("⚠️ Structured parsing yielded few comments, using fallback method...")
            comments.extend(self._extract_fallback_comments(analysis, files[:5]))
        
        logger.info(f"✅ Parsed {len(comments)} comments from analysis")
        # Count suggestions
        suggestions_count = sum(1 for comment in comments if comment.has_suggestion())
        if suggestions_count > 0:
            logger.info(f"✨ {suggestions_count} comments include code suggestions")
        
        return comments[:8]  # Limit to 8 comments max

    def _is_comment_complete(self, comment_dict: dict) -> bool:
        """Check if a comment has the minimum required fields"""
        return all(k in comment_dict for k in ['file', 'line', 'comment'])

    def _create_review_comment(self, comment_dict: dict, original_lines: List[str], suggested_lines: List[str]) -> ReviewComment:
        """Create a ReviewComment object from parsed data"""
        if not self._is_comment_complete(comment_dict):
            return None
            
        # Determine if this is a suggestion
        has_suggestion = len(original_lines) > 0 and len(suggested_lines) > 0
        
        # Clean up code blocks (remove extra whitespace/empty lines)
        original_code = None
        suggested_code = None
        suggestion_type = None
        
        if has_suggestion:
            original_code = '\n'.join(original_lines).strip()
            suggested_code = '\n'.join(suggested_lines).strip()
            
            # Determine suggestion type
            if comment_dict.get('end_line') and comment_dict['end_line'] > comment_dict['line']:
                suggestion_type = "multi_line"
            else:
                suggestion_type = "single_line"
        
        return ReviewComment(
            file_path=comment_dict['file'],
            line_number=comment_dict['line'],
            body=comment_dict['comment'],
            severity=comment_dict.get('severity', 'info'),
            suggestion_type=suggestion_type,
            original_code=original_code,
            suggested_code=suggested_code,
            end_line_number=comment_dict.get('end_line')
        )
    
    def _extract_fallback_comments(self, analysis: str, files: List[dict]) -> List[ReviewComment]:
        """Fallback method to extract comments when structured parsing fails"""
        logger.debug("🔄 Using fallback comment extraction...")
        
        comments = []
        sentences = re.split(r'[.!?]+', analysis)
        
        # Look for actionable sentences and map them to files
        for sentence in sentences[:10]:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            # Check if sentence mentions any file
            mentioned_file = None
            for file_info in files:
                if file_info['filename'] in sentence or file_info['filename'].split('.')[-1] in sentence:
                    mentioned_file = file_info
                    break
            
            # Create comments for files with actionable feedback
            if mentioned_file and any(keyword in sentence.lower() for keyword in [
                'should', 'could', 'consider', 'recommend', 'suggest', 'improve', 
                'issue', 'problem', 'vulnerability', 'performance', 'optimize'
            ]):
                comments.append(ReviewComment(
                    file_path=mentioned_file['filename'],
                    line_number=1,  # Default to line 1 for fallback
                    body=f"📝 **Review Suggestion:**\n\n{sentence.strip()}\n\n*This comment was generated from AI analysis.*",
                    severity="info"
                ))
        
        # If still no good comments, create at least one summary comment for the main file
        if not comments and files:
            main_file = files[0]  # Use the first file
            comments.append(ReviewComment(
                file_path=main_file['filename'],
                line_number=1,
                body=f"📋 **AI Review Summary:**\n\n{analysis[:500]}...\n\n*Please review the changes for potential improvements.*",
                severity="info"
            ))
        
        return comments
    
    def _build_analysis_prompt(self, diff: str, pr_info: dict, review_type: str) -> str:
        """Build analysis prompt based on review type"""
        logger.debug(f"🔨 Building {review_type} analysis prompt...")
        
        base_prompt = f"""
You are an expert code reviewer. Analyze this pull request:

**PR Info:**
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info.get('author', 'N/A')}
- Files changed: {pr_info.get('files_changed', 0)}
- Additions: +{pr_info.get('additions', 0)} lines
- Deletions: -{pr_info.get('deletions', 0)} lines

**Diff:**
```
{diff}
```

"""
        
        if review_type == "security":
            prompt = base_prompt + """
Focus on security vulnerabilities:
- Look for SQL injection, XSS, authentication issues
- Check for hardcoded secrets or credentials
- Identify unsafe input handling
- Flag potential authorization bypasses
"""
            logger.debug("✅ Built security-focused prompt")
        elif review_type == "performance":
            prompt = base_prompt + """
Focus on performance issues:
- Identify inefficient algorithms or database queries
- Look for memory leaks or resource management issues
- Check for unnecessary computations or network calls
- Suggest optimization opportunities
"""
            logger.debug("✅ Built performance-focused prompt")
        elif review_type == "maintainability":
            prompt = base_prompt + """
Focus on code maintainability:
- Check code organization and structure
- Look for code duplication
- Assess naming conventions and documentation
- Identify areas that need refactoring
"""
            logger.debug("✅ Built maintainability-focused prompt")
        else:  # categorized (default)
            prompt = base_prompt + """
Provide a comprehensive review covering:
1. **Security** - Any security concerns or vulnerabilities
2. **Performance** - Potential performance issues or improvements
3. **Code Quality** - Maintainability, readability, best practices
4. **Logic** - Correctness of the implementation
5. **Testing** - Are there adequate tests for the changes?

Format as sections with specific examples from the code.
"""
            logger.debug("✅ Built categorized (comprehensive) prompt")
        
        return prompt + "\nProvide actionable feedback with specific line references where possible." 