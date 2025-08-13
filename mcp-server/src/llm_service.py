"""
LLM Service for generating Draw.io XML diagrams using Claude API.
"""
import asyncio
import hashlib
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, Optional

import anthropic
from anthropic import APIError, APIConnectionError, APITimeoutError, RateLimitError

from .exceptions import LLMError, LLMErrorCode


@dataclass
class CacheEntry:
    """Cache entry for LLM responses."""
    xml: str
    timestamp: float
    expires_at: float


class LLMService:
    """Service for generating Draw.io XML diagrams using Claude API."""
    
    def __init__(self, api_key: Optional[str] = None, skip_client_init: bool = False):
        """
        Initialize the LLM service.
        
        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
            skip_client_init: If True, skip Anthropic client initialization (for testing)
            
        Raises:
            LLMError: If API key is missing.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY environment variable is required",
                LLMErrorCode.API_KEY_MISSING
            )
        
        # Check if this is a test/fake key
        self.is_test_key = self._is_test_key(self.api_key)
        
        if not skip_client_init:
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=25.0  # 25 second timeout for API calls
            )
        else:
            self.client = None
        
        # Cache configuration
        self.cache: Dict[str, CacheEntry] = {}
        self.CACHE_TTL = 60 * 60  # 1 hour in seconds
        self.MAX_CACHE_SIZE = 100
        
        # Start cache cleanup task
        self._start_cache_cleanup()
    
    def _is_test_key(self, api_key: str) -> bool:
        """
        Check if the API key appears to be a test/fake key.
        
        Args:
            api_key: The API key to check
            
        Returns:
            bool: True if the key appears to be for testing
        """
        if not api_key:
            return False
        
        api_key_lower = api_key.lower()
        test_patterns = [
            "test", "fake", "12345", "testing", "example", "demo"
        ]
        
        return any(pattern in api_key_lower for pattern in test_patterns)
    
    async def generate_drawio_xml(self, prompt: str) -> str:
        """
        Generate Draw.io XML from natural language prompt.
        
        Args:
            prompt: Natural language description of the diagram.
            
        Returns:
            Valid Draw.io XML string.
            
        Raises:
            LLMError: If generation fails for any reason.
        """
        try:
            # Check if client is available
            if not self.client:
                raise LLMError(
                    "LLM client not initialized - cannot generate diagrams",
                    LLMErrorCode.API_KEY_MISSING
                )
            
            # Warn if using test key
            if self.is_test_key:
                raise LLMError(
                    "Cannot generate diagrams with test/fake API key. Please provide a valid Anthropic API key.",
                    LLMErrorCode.API_KEY_MISSING
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(prompt)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(prompt)
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet
                max_tokens=8192,
                temperature=0.2,  # Lower temperature for more consistent results
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )
            
            # Extract XML from response
            content = response.content[0]
            if content.type != "text":
                raise LLMError(
                    "Received unexpected response format from Claude API",
                    LLMErrorCode.INVALID_RESPONSE
                )
            
            xml = self._extract_xml_from_response(content.text)
            self._validate_drawio_xml(xml)
            
            # Cache the result
            self._save_to_cache(cache_key, xml)
            
            return xml
            
        except LLMError:
            # Re-raise LLMError as-is
            raise
        except Exception as error:
            # Handle all errors through the error handler
            raise self._handle_anthropic_error(error)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Draw.io XML generation."""
        return """You are an expert at generating Draw.io XML format. Convert the user's natural language diagram description into valid XML format that can be opened in Draw.io (diagrams.net).

Important requirements:
1. Always output in valid Draw.io XML format
2. XML must start with <mxfile> tag and end with </mxfile> tag
3. Define diagram elements using <mxCell> tags
4. Set appropriate coordinates and sizes
5. Handle text content correctly
6. Choose appropriate diagram types like flowcharts, org charts, system diagrams, etc.
7. For AWS architecture diagrams, follow the "AWS Diagram Rules" below

AWS Diagram Rules:
 1. Use draw.io "AWS 2025" icons
 2. Don't overlay text on borders or icons. Create margins to improve visibility
 3. Standardize icon size to 48×48
 4. Icon descriptions should include:
    4-1. Service name
    4-2. Resource name (do not include IDs)
 5. Express boundaries as follows:
    5-1. AWS Cloud
    5-2. Region
    5-3. VPC (add CIDR in parentheses at the end)
    5-4. Availability Zone
    5-5. Subnet (add CIDR in parentheses at the end)
    5-6. Security Group
 6. Leave ample margins in boundaries considering scalability
 7. Place icons close together for better visibility

Output format:
- Output XML only (no explanatory text needed)
- XML must be properly formatted
- Use UTF-8 character encoding

Basic Draw.io XML structure example:
```xml
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI" version="22.1.0">
  <diagram name="Page-1" id="page-id">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Place diagram elements here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```"""
    
    def _build_user_prompt(self, prompt: str) -> str:
        """Build user prompt with the specific diagram request."""
        return f"""Generate Draw.io XML format based on the following description:

{prompt}

Requirements:
- Express the above description as an appropriate diagram
- Clearly show relationships between elements
- Create a readable layout
- Handle labels and text correctly

Output XML only:"""
    
    def _handle_anthropic_error(self, error: Exception) -> LLMError:
        """Handle Anthropic API specific errors."""
        error_message = str(error).lower()
        
        # Rate limit errors
        if isinstance(error, RateLimitError) or "rate limit" in error_message or "429" in error_message:
            return LLMError(
                "AI service rate limit reached. Please wait and try again",
                LLMErrorCode.RATE_LIMIT_ERROR,
                error
            )
        
        # Quota exceeded errors
        if "quota" in error_message or "billing" in error_message or "credits" in error_message:
            return LLMError(
                "AI service usage limit reached. Please contact administrator",
                LLMErrorCode.QUOTA_EXCEEDED,
                error
            )
        
        # Timeout errors
        if isinstance(error, APITimeoutError) or ("timeout" in error_message and 
                                                  "connection" not in error_message and 
                                                  "network" not in error_message):
            return LLMError(
                "AI service response timed out. Please try again",
                LLMErrorCode.TIMEOUT_ERROR,
                error
            )
        
        # Connection/network errors
        if (isinstance(error, APIConnectionError) or 
            any(term in error_message for term in ["network", "connection", "econnreset", "enotfound", "fetch"])):
            return LLMError(
                "Cannot connect to AI service. Please check network connection and try again",
                LLMErrorCode.CONNECTION_ERROR,
                error
            )
        
        # Authentication errors
        if any(term in error_message for term in ["unauthorized", "authentication", "api key", "401"]):
            return LLMError(
                "AI service authentication failed. Please check configuration",
                LLMErrorCode.API_KEY_MISSING,
                error
            )
        
        # Default to unknown error
        return LLMError(
            "An error occurred with the AI service. Please wait and try again",
            LLMErrorCode.UNKNOWN_ERROR,
            error
        )
    
    def _extract_xml_from_response(self, response: str) -> str:
        """Extract XML content from Claude's response."""
        # Look for XML content between ```xml tags or direct XML
        xml_match = re.search(r'```xml\s*([\s\S]*?)\s*```', response) or \
                   re.search(r'(<mxfile[\s\S]*?</mxfile>)', response)
        
        if xml_match:
            return xml_match.group(1).strip()
        
        # If no XML tags found, check if the entire response is XML
        response_stripped = response.strip()
        if response_stripped.startswith('<mxfile') and response_stripped.endswith('</mxfile>'):
            return response_stripped
        
        raise LLMError(
            "AI could not generate a valid diagram. Please try a different description",
            LLMErrorCode.INVALID_RESPONSE
        )
    
    def _validate_drawio_xml(self, xml: str) -> None:
        """Basic validation of Draw.io XML structure."""
        try:
            # Check for required root elements
            if '<mxfile' not in xml:
                raise LLMError(
                    "Generated XML is invalid: mxfile tag not found",
                    LLMErrorCode.INVALID_XML
                )
            
            if '</mxfile>' not in xml:
                raise LLMError(
                    "Generated XML is invalid: mxfile closing tag not found",
                    LLMErrorCode.INVALID_XML
                )
            
            if '<mxGraphModel' not in xml:
                raise LLMError(
                    "Generated XML is invalid: mxGraphModel tag not found",
                    LLMErrorCode.INVALID_XML
                )
            
            if '<root>' not in xml:
                raise LLMError(
                    "Generated XML is invalid: root tag not found",
                    LLMErrorCode.INVALID_XML
                )
            
            # Basic XML structure validation
            open_tags = len(re.findall(r'<[^/][^>]*>', xml))
            close_tags = len(re.findall(r'</[^>]*>', xml))
            self_closing_tags = len(re.findall(r'<[^>]*/>', xml))
            
            # Self-closing tags count as both open and close
            # Note: We don't throw error for tag balance issues as it might be a false positive
            
            # Check for minimum content (at least one cell beyond the root cells)
            cell_matches = re.findall(r'<mxCell', xml)
            # Empty diagrams might be valid - don't throw error
            
        except LLMError:
            raise
        except Exception as error:
            raise LLMError(
                "Error occurred during XML validation",
                LLMErrorCode.INVALID_XML,
                error
            )
    
    def _generate_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        # Use SHA-256 hash for cache key
        hash_obj = hashlib.sha256(prompt.encode('utf-8'))
        return f"llm_{hash_obj.hexdigest()[:16]}"
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get result from cache if valid."""
        entry = self.cache.get(key)
        if not entry:
            return None
        
        if time.time() > entry.expires_at:
            del self.cache[key]
            return None
        
        return entry.xml
    
    def _save_to_cache(self, key: str, xml: str) -> None:
        """Save result to cache."""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.MAX_CACHE_SIZE:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]
        
        now = time.time()
        self.cache[key] = CacheEntry(
            xml=xml,
            timestamp=now,
            expires_at=now + self.CACHE_TTL
        )
    
    def _clean_cache(self) -> None:
        """Clean expired cache entries."""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry.expires_at
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def _start_cache_cleanup(self) -> None:
        """Start periodic cache cleanup task."""
        def cleanup_task():
            while True:
                time.sleep(10 * 60)  # Every 10 minutes
                self._clean_cache()
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.MAX_CACHE_SIZE
        }