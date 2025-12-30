import json
import logging
from typing import AsyncGenerator, List, Optional, Dict, Any
from datetime import datetime

from src.core.interfaces import ILLMProvider, IVectorStore
from src.core.constants import (
    CONVERSATION_HISTORY_LIMIT,
    AUTO_TITLE_MAX_LENGTH,
    MAX_TOOL_ITERATIONS,
    RAG_TOP_K_DOCUMENTS,
)
from src.core.prompts import build_system_prompt
from src.models.database import Conversation, Message, Project
from src.models.schemas import ChatRequest, ChatResponse, MessageResponse
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.project_repository import ProjectRepository
from src.utils.token_counter import estimate_tokens
from src.utils.query_classifier import classify_query
from src.utils.hallucination_detector import detect_hallucination_risk, prepend_warning
from src.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        llm_provider: ILLMProvider,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        project_repo: ProjectRepository,
        vector_store: Optional[IVectorStore] = None,
    ):
        self.llm_provider = llm_provider
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.project_repo = project_repo
        self.vector_store = vector_store

    async def chat(self, request: ChatRequest) -> ChatResponse:
        conversation = self.conversation_repo.get_or_create(
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            title=request.message[:AUTO_TITLE_MAX_LENGTH] if not request.conversation_id else None,
        )

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            message_type="text",
            token_count=estimate_tokens(request.message),
        )
        saved_user_message = self.message_repo.create(user_message)

        history = self.message_repo.get_recent_messages(conversation.id, limit=10)
        
        # Get project for system prompt and tools
        project = self.project_repo.find_by_id(request.project_id)
        
        logger.info(f"🔍 RAG: Retrieving context for project={request.project_id}, docs={request.document_ids}")
        document_context = await self._get_document_context(
            request.project_id, request.message, request.document_ids
        )
        
        if document_context:
            logger.info(f"✅ RAG: Found context ({len(document_context)} chars)")
        else:
            logger.warning(f"⚠️ RAG: No document context found")
        
        system_prompt = project.system_prompt if project else None
        
        # Execute tool loop to get final response
        ai_response = await self._execute_tool_loop(
            message=request.message,
            history=history,
            document_context=document_context,
            system_prompt=system_prompt,
            project=project,
            use_gpu=request.use_gpu,
            model=request.model
        )

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response,
            message_type="text",
            token_count=estimate_tokens(ai_response),
        )
        saved_assistant_message = self.message_repo.create(assistant_message)
        
        # Update conversation total tokens
        conversation.total_tokens = conversation.total_tokens + estimate_tokens(request.message) + estimate_tokens(ai_response)
        self.conversation_repo.update(conversation)

        # Generate AI title for new conversations after first exchange
        if not request.conversation_id and not conversation.title:
            await self._generate_ai_title(conversation, request.message)

        return ChatResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(saved_user_message),
            response=MessageResponse.model_validate(saved_assistant_message),
        )

    async def _execute_tool_loop(
        self,
        message: str,
        history: List[Message],
        document_context: Optional[str],
        system_prompt: Optional[str],
        project: Optional[Project],
        use_gpu: bool = True,
        model: Optional[str] = None,
        max_iterations: int = MAX_TOOL_ITERATIONS
    ) -> str:
        """
        Execute agentic loop with tool calling.
        
        Returns final text response from LLM.
        """
        from ..tools.langchain_tools import get_langchain_tools
        tool_registry = get_tool_registry()
        
        # Track tools used for hallucination detection
        tools_used = []
        
        # Get enabled tools for this project (as LangChain tool objects)
        tools = None
        enabled_tool_names = project.tools if project and project.tools else []
        if enabled_tool_names:
            tools = get_langchain_tools(enabled_tool_names)
            if tools:
                logger.info(f"🔧 Tools: Enabled {len(tools)} tools: {enabled_tool_names}")
        
        # Classify query for logging only (tools passed via bind_tools, not prompt)
        query_type, tool_requirement = classify_query(message)
        logger.info(f"📋 Query classified as: {query_type.value}, requirement: {tool_requirement.value}")
        
        # ===== FORCE WEB SEARCH FOR URL QUERIES =====
        from ..utils.query_classifier import detect_url_patterns, extract_url_or_domain, QueryType, ToolRequirement
        
        if (query_type == QueryType.URL_LOOKUP and 
            tool_requirement == ToolRequirement.REQUIRED and 
            "web_search" in enabled_tool_names):
            
            logger.info(f"🌐 URL detected - forcing web_search before LLM processing")
            
            # Extract domain/URL for search
            search_target = extract_url_or_domain(message)
            logger.info(f"🔍 Extracted search target: {search_target}")
            
            # Execute web_search immediately
            try:
                tool_result = await tool_registry.execute_tool("web_search", query=search_target, num_results=5)
                tools_used.append("web_search")
                
                if tool_result.success:
                    logger.info(f"✅ Pre-search complete: {len(tool_result.result)} chars retrieved")
                    
                    # Inject search results into document context
                    search_context = f"\n\n=== WEB SEARCH RESULTS FOR {search_target} ===\n{tool_result.result}\n=== END SEARCH RESULTS ===\n"
                    document_context = search_context + (document_context or "")
                    
                    # Save web search results as document for sidebar
                    if tool_result.metadata and tool_result.metadata.get("results"):
                        import asyncio
                        asyncio.create_task(self._save_web_search_as_document(
                            project_id=project.id,
                            query=tool_result.metadata.get("query", search_target),
                            results=tool_result.metadata.get("results", [])
                        ))
                        logger.info(f"📄 Creating document for web search: {search_target}")
                    
                    # Modify system prompt to enforce result usage
                    system_prompt = (
                        f"{system_prompt or ''}\n\n"
                        f"CRITICAL INSTRUCTION: The user asked about a URL/website ({search_target}). "
                        f"Current web search results have been provided above in the context. "
                        f"You MUST base your answer ONLY on these search results. "
                        f"DO NOT add information from your training data. "
                        f"If the search results don't contain enough information, say so explicitly."
                    )
                else:
                    logger.warning(f"⚠️ Pre-search failed: {tool_result.error}")
                    
            except Exception as e:
                logger.error(f"❌ Pre-search execution failed: {str(e)}", exc_info=True)
        
        # Build system prompt (tools passed separately via bind_tools)
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_system_prompt = build_system_prompt(
            current_date=current_date,
            project_prompt=system_prompt,
            enabled_tools=enabled_tool_names,
            subject=project.name if project else "various subjects"
        )
        
        # Build initial prompt with system instructions
        prompt = self._build_prompt(message, history, document_context, enhanced_system_prompt)
        
        # Tool execution loop
        for iteration in range(max_iterations):
            logger.info(f"🔄 Tool loop: Iteration {iteration + 1}/{max_iterations}")
            
            # Call LLM with current context and tools
            response = await self.llm_provider.generate(prompt, tools=tools)
            
            # Check if response is a tool call
            if isinstance(response, dict) and response.get("type") == "tool_call":
                tool_name = response["tool_name"]
                tool_args = response["tool_args"]
                logger.info(f"🔧 Tool call: {tool_name}({tool_args})")
                
                # Track tool usage
                tools_used.append(tool_name)
                
                # Execute tool
                try:
                    tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
                    
                    if tool_result.success:
                        logger.info(f"✅ Tool result: {tool_result.result[:100]}...")
                        result_text = tool_result.result
                    else:
                        logger.error(f"❌ Tool error: {tool_result.error}")
                        result_text = f"Error executing {tool_name}: {tool_result.error}"
                    
                except Exception as e:
                    logger.error(f"❌ Tool execution failed: {str(e)}", exc_info=True)
                    result_text = f"Error executing {tool_name}: {str(e)}"
                
                # Add tool result to prompt for next iteration
                prompt += f"\n\nTool {tool_name} returned: {result_text}\n\nBased on this information, provide your response to the user:"
                continue
            
            # Text response - check for hallucination risk
            logger.info(f"✅ Final response generated (iteration {iteration + 1})")
            
            # Detect potential hallucinations
            warning = detect_hallucination_risk(message, response, tools_used)
            if warning:
                logger.warning(f"⚠️ Hallucination risk detected, adding warning")
                response = prepend_warning(response, warning)
            
            return response
        
        # Max iterations reached
        logger.warning(f"⚠️ Max iterations ({max_iterations}) reached in tool loop")
        return "I apologize, but I reached the maximum number of steps while processing your request. Please try rephrasing your question."
    
    async def _execute_tool_loop_stream(
        self,
        message: str,
        history: List[Message],
        document_context: Optional[str],
        system_prompt: Optional[str],
        project: Optional[Project],
        use_gpu: bool = True,
        model: Optional[str] = None,
        max_iterations: int = MAX_TOOL_ITERATIONS
    ) -> AsyncGenerator[Any, None]:
        """
        Execute agentic loop with tool calling and streaming support.
        
        HYBRID APPROACH:
        - Use .invoke() (non-streaming) for tool selection
        - Execute tools with status messages
        - Use .astream() (streaming) for final response
        
        Yields text chunks for streaming and tool execution status.
        """
        from ..tools.langchain_tools import get_langchain_tools
        tool_registry = get_tool_registry()
        
        # Track tools used for hallucination detection
        tools_used = []
        
        # Track if we forced a tool execution (skip tool loop if true)
        forced_tool_execution = False
        
        # Get enabled tools for this project (as LangChain tool objects)
        tools = None
        enabled_tool_names = project.tools if project and project.tools else []
        if enabled_tool_names:
            tools = get_langchain_tools(enabled_tool_names)
            if tools:
                logger.info(f"🔧 Tools: Enabled {len(tools)} tools: {enabled_tool_names}")
        
        # Classify query for logging only (tools passed via bind_tools, not prompt)
        query_type, tool_requirement = classify_query(message)
        logger.info(f"📋 Query classified as: {query_type.value}, requirement: {tool_requirement.value}")
        
        # ===== FORCE WEB SEARCH FOR URL QUERIES =====
        from ..utils.query_classifier import detect_url_patterns, extract_url_or_domain, QueryType, ToolRequirement
        
        if (query_type == QueryType.URL_LOOKUP and 
            tool_requirement == ToolRequirement.REQUIRED and 
            "web_search" in enabled_tool_names):
            
            logger.info(f"🌐 URL detected - forcing web_search before LLM processing")
            
            # Extract domain/URL for search
            search_target = extract_url_or_domain(message)
            logger.info(f"🔍 Extracted search target: {search_target}")
            
            # Yield structured status message (matches tool loop format)
            yield {
                "type": "tool_execution",
                "tool": "web_search",
                "status": "executing",
                "args": {"query": search_target, "num_results": 5}
            }
            
            # Execute web_search immediately
            try:
                tool_result = await tool_registry.execute_tool("web_search", query=search_target, num_results=5)
                tools_used.append("web_search")
                
                if tool_result.success:
                    logger.info(f"✅ Pre-search complete: {len(tool_result.result)} chars retrieved")
                    
                    # Mark that we forced tool execution
                    forced_tool_execution = True
                    
                    # Yield structured success message
                    yield {
                        "type": "tool_result",
                        "tool": "web_search",
                        "status": "success",
                        "result": tool_result.result[:200]  # Truncate for display
                    }
                    
                    # Inject search results into document context
                    search_context = f"\n\n=== WEB SEARCH RESULTS FOR {search_target} ===\n{tool_result.result}\n=== END SEARCH RESULTS ===\n"
                    document_context = search_context + (document_context or "")
                    
                    # Save web search results as document for sidebar
                    if tool_result.metadata and tool_result.metadata.get("results"):
                        import asyncio
                        asyncio.create_task(self._save_web_search_as_document(
                            project_id=project.id,
                            query=tool_result.metadata.get("query", search_target),
                            results=tool_result.metadata.get("results", [])
                        ))
                        logger.info(f"📄 Creating document for web search: {search_target}")
                    
                    # Modify system prompt to enforce result usage
                    system_prompt = (
                        f"{system_prompt or ''}\n\n"
                        f"CRITICAL INSTRUCTION: The user asked about a URL/website ({search_target}). "
                        f"Current web search results have been provided above in the context. "
                        f"You MUST base your answer ONLY on these search results. "
                        f"DO NOT add information from your training data. "
                        f"If the search results don't contain enough information, say so explicitly."
                    )
                else:
                    logger.warning(f"⚠️ Pre-search failed: {tool_result.error}")
                    # Yield structured error message
                    yield {
                        "type": "tool_result",
                        "tool": "web_search",
                        "status": "error",
                        "result": tool_result.error
                    }
                    
            except Exception as e:
                logger.error(f"❌ Pre-search execution failed: {str(e)}", exc_info=True)
                # Yield structured error message
                yield {
                    "type": "tool_result",
                    "tool": "web_search",
                    "status": "error",
                    "result": str(e)
                }
        
        # Build system prompt (tools passed separately via bind_tools)
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_system_prompt = build_system_prompt(
            current_date=current_date,
            project_prompt=system_prompt,
            enabled_tools=enabled_tool_names,
            subject=project.name if project else "various subjects"
        )
        
        # Build initial prompt with system instructions
        prompt = self._build_prompt(message, history, document_context, enhanced_system_prompt)
        
        # Skip tool loop if we already forced tool execution (avoids timeout with slow models)
        if forced_tool_execution:
            logger.info(f"⚡ Skipping tool loop - already forced web_search execution")
            logger.info(f"💬 Streaming final response directly")
            
            # Stream the final response without tool decision
            async for chunk in self.llm_provider.generate_stream(prompt, model=model, use_gpu=use_gpu):
                yield chunk
            
            logger.info(f"✅ Response complete (forced tool path)")
            return
        
        # Tool execution loop
        for iteration in range(max_iterations):
            logger.info(f"🔄 Tool loop: Iteration {iteration + 1}/{max_iterations}")
            
            # STEP 1: Use invoke() to check if model wants to use tools (fast, non-streaming)
            try:
                response = await self.llm_provider.generate(prompt, tools=tools, model=model, use_gpu=use_gpu)
            except Exception as e:
                logger.error(f"❌ LLM error: {str(e)}")
                yield {"type": "error", "message": str(e)}
                return
            
            # STEP 2: Check if response is a tool call
            if isinstance(response, dict) and response.get("type") == "tool_call":
                tool_name = response["tool_name"]
                tool_args = response["tool_args"]
                logger.info(f"🔧 Tool call: {tool_name}({tool_args})")
                
                # Track tool usage
                tools_used.append(tool_name)
                
                # Send tool execution status (will persist in UI)
                yield {
                    "type": "tool_execution",
                    "tool": tool_name,
                    "status": "executing",
                    "args": tool_args
                }
                
                # Execute tool
                try:
                    tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
                    
                    if tool_result.success:
                        logger.info(f"✅ Tool result: {tool_result.result[:100]}...")
                        result_text = tool_result.result
                        status = "success"
                        
                        # Auto-save web_search results as document (asynchronously to avoid blocking stream)
                        if tool_name == "web_search" and project and tool_result.metadata:
                            import asyncio
                            asyncio.create_task(self._save_web_search_as_document(
                                project_id=project.id,
                                query=tool_result.metadata.get("query", ""),
                                results=tool_result.metadata.get("results", [])
                            ))
                    else:
                        logger.error(f"❌ Tool error: {tool_result.error}")
                        result_text = f"Error executing {tool_name}: {tool_result.error}"
                        status = "error"
                    
                except Exception as e:
                    logger.error(f"❌ Tool execution failed: {str(e)}", exc_info=True)
                    result_text = f"Error executing {tool_name}: {str(e)}"
                    status = "error"
                
                # Send tool completion status (will persist in UI)
                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "status": status,
                    "result": result_text[:200]  # Truncate for display
                }
                
                # Add tool result to prompt for next iteration with emphasis on citations
                if tool_name == "web_search":
                    prompt += f"\n\nTool {tool_name} returned: {result_text}\n\nIMPORTANT: In your response, cite the URLs from the search results. Format each source as a markdown link: [Title](URL). Provide a comprehensive answer with clickable source links."
                else:
                    prompt += f"\n\nTool {tool_name} returned: {result_text}\n\nBased on this information, provide your response to the user:"
                continue
            
            # STEP 3: Text response - stream it to user
            logger.info(f"💬 Streaming final response (iteration {iteration + 1})")
            
            # Collect full response for hallucination detection
            full_response = ""
            
            # Stream the response WITHOUT tools (faster)
            async for chunk in self.llm_provider.generate_stream(prompt, tools=None, model=model, use_gpu=use_gpu):
                if isinstance(chunk, dict) and chunk.get("type") == "error":
                    logger.error(f"❌ Streaming error: {chunk.get('message')}")
                    yield chunk
                    return
                else:
                    full_response += chunk
                    yield chunk
            
            # Check for hallucination risk after streaming
            warning = detect_hallucination_risk(message, full_response, tools_used)
            if warning:
                logger.warning(f"⚠️ Hallucination risk detected, sending warning")
                yield {"type": "warning", "content": warning}
            
            # Done!
            logger.info(f"✅ Response complete (iteration {iteration + 1})")
            return
        
        # Max iterations reached
        logger.warning(f"⚠️ Max iterations ({max_iterations}) reached in tool loop")
        yield "I apologize, but I reached the maximum number of steps while processing your request. Please try rephrasing your question."
    
    async def _save_web_search_as_document(
        self,
        project_id: int,
        query: str,
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Save web search results as a markdown document in the project.
        This preserves URLs and sources for future reference.
        Uses a new DB session to avoid conflicts with the streaming context.
        """
        try:
            from datetime import datetime
            import io
            from src.models.database import get_db
            from src.services.document_service import DocumentService
            from src.repositories.document_repository import DocumentRepository
            from src.providers.chroma_provider import ChromaProvider
            
            # Generate markdown content with clickable links
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            markdown_content = f"""# Web Search: {query}

**Search Date:** {timestamp}  
**Number of Results:** {len(results)}

---

"""
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No description available")
                url = result.get("url", "")
                engine = result.get("engine", "unknown")
                
                markdown_content += f"""## {i}. [{title}]({url})

**Source:** {engine}

{snippet}

---

"""
            
            markdown_content += f"\n*This document was automatically created by the web_search tool.*\n"
            
            # Create filename
            safe_query = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in query)
            safe_query = safe_query[:50]  # Limit length
            filename = f"websearch_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            # Use a NEW DB session (not the streaming context session)
            db_gen = get_db()
            db = next(db_gen)
            try:
                doc_repo = DocumentRepository(db)
                vector_store = ChromaProvider()
                doc_service = DocumentService(doc_repo, vector_store)
                
                # Convert markdown string to file-like object
                file_content = io.BytesIO(markdown_content.encode('utf-8'))
                
                # Upload document
                await doc_service.upload_document(
                    project_id=project_id,
                    file=file_content,
                    filename=filename,
                    file_type="text/markdown"
                )
                
                logger.info(f"✅ Created document '{filename}' with {len(results)} search results")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"⚠️ Failed to save search results as document: {str(e)}", exc_info=True)
    
    async def _generate_ai_title(self, conversation: Conversation, first_message: str) -> None:
        """Generate a concise title using AI based on first message"""
        try:
            title_prompt = f"Generate a short, concise 3-6 word title for a conversation that starts with: '{first_message[:200]}'. Reply with ONLY the title, no quotes or punctuation."
            title = await self.llm_provider.generate(title_prompt)
            # Clean up the title
            title = title.strip().strip('"').strip("'")
            if len(title) > 100:
                title = title[:97] + "..."
            conversation.title = title
            self.conversation_repo.update(conversation)
        except Exception as e:
            # Fallback to simple title if AI generation fails
            conversation.title = first_message[:50]
            self.conversation_repo.update(conversation)

    async def _get_document_context(
        self, project_id: int, query: str, document_ids: Optional[List[int]] = None
    ) -> Optional[str]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.vector_store:
            logger.warning("⚠️ RAG: No vector store available")
            return None
        
        # If no documents selected, don't load any context
        if not document_ids or len(document_ids) == 0:
            logger.info("📭 RAG: No documents selected, skipping context retrieval")
            return None
        
        try:
            # ChromaDB filter - must use simple equality or $or/$and
            if len(document_ids) == 1:
                # Single document filter
                filter_dict = {
                    "$and": [
                        {"project_id": {"$eq": project_id}},
                        {"document_id": {"$eq": document_ids[0]}}
                    ]
                }
            else:
                # Multiple documents - use $or
                filter_dict = {
                    "$and": [
                        {"project_id": {"$eq": project_id}},
                        {
                            "$or": [
                                {"document_id": {"$eq": doc_id}} 
                                for doc_id in document_ids
                            ]
                        }
                    ]
                }
            
            logger.info(f"🔍 RAG: Searching with filter={filter_dict}")
            
            # Use LangChain search with filter
            results = await self.vector_store.search(
                query=query, 
                top_k=RAG_TOP_K_DOCUMENTS,
                filter=filter_dict
            )
            
            logger.info(f"📊 RAG: Search returned {len(results)} results")
            
            if not results:
                logger.warning("⚠️ RAG: No results from vector search")
                return None
            
            # Build context from results
            # Group by filename to show we're using ONE document
            filenames = set(r.get("metadata", {}).get("filename", "Unknown") for r in results[:3])
            context_parts = [f"Based on the following document: {', '.join(filenames)}"]
            context_parts.append("\nRelevant excerpts:")
            
            for i, result in enumerate(results[:3], 1):
                doc_text = result.get("document", "")
                filename = result.get("metadata", {}).get("filename", "Unknown")
                score = result.get("score", 0)
                
                context_parts.append(f"\n[Excerpt {i} (relevance: {score:.2f})]")
                context_parts.append(doc_text[:500])
            
            context = "\n".join(context_parts)
            logger.info(f"✅ RAG: Built context with {len(context_parts)-1} chunks")
            return context
        except Exception as e:
            logger.error(f"❌ RAG: Error retrieving document context: {str(e)}", exc_info=True)
            return None

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat responses with tool execution support."""
        conversation = self.conversation_repo.get_or_create(
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            title=request.message[:AUTO_TITLE_MAX_LENGTH] if not request.conversation_id else None,
        )

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            message_type="text",
            token_count=estimate_tokens(request.message),
        )
        saved_user_message = self.message_repo.create(user_message)

        history = self.message_repo.get_recent_messages(conversation.id, limit=CONVERSATION_HISTORY_LIMIT)
        
        # Get project for system prompt and tools
        project = self.project_repo.find_by_id(request.project_id)
        
        document_context = await self._get_document_context(
            request.project_id, request.message, request.document_ids
        )
        
        system_prompt = project.system_prompt if project else None
        
        # Execute tool loop with streaming
        full_response = ""
        async for chunk in self._execute_tool_loop_stream(
            message=request.message,
            history=history,
            document_context=document_context,
            system_prompt=system_prompt,
            project=project,
            use_gpu=request.use_gpu,
            model=request.model
        ):
            if isinstance(chunk, dict):
                # Tool execution status or final done message
                yield f"data: {json.dumps(chunk)}\n\n"
            else:
                # Text chunk
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
            message_type="text",
            token_count=estimate_tokens(full_response),
        )
        saved_assistant_message = self.message_repo.create(assistant_message)
        
        # Update conversation total tokens
        conversation.total_tokens = conversation.total_tokens + estimate_tokens(request.message) + estimate_tokens(full_response)
        self.conversation_repo.update(conversation)
        
        # Generate AI title for new conversations after first exchange
        if not request.conversation_id and not conversation.title:
            await self._generate_ai_title(conversation, request.message)
        
        yield f"data: {json.dumps({'done': True, 'conversation_id': conversation.id})}\n\n"

    def _build_prompt(self, message: str, history: List[Message], document_context: Optional[str], system_prompt: Optional[str] = None) -> str:
        """
        Build prompt with context. System prompt is now built via build_system_prompt().
        This method adds document context, history, and current message.
        """
        prompt_parts = []
        
        # Add enhanced system prompt (already built with all rules)
        if system_prompt:
            prompt_parts.append(system_prompt)
        
        # Add document context if available
        if document_context:
            prompt_parts.append(f"\nContext from uploaded documents:\n{document_context}")
        
        # Add conversation history
        if history:
            prompt_parts.append("\nPrevious conversation:")
            for msg in history:
                role = "User" if msg.role == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg.content}")
        
        # Add current message
        prompt_parts.append(f"\nCurrent question: {message}\nAssistant:")
        
        return "\n".join(prompt_parts)
