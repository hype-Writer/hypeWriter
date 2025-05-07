"""Define the API client for book generation system using Google Gemini"""

import google.generativeai as genai
from typing import Dict, List, Optional, Iterable
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class BookAgents:
    def __init__(self, agent_config: Dict, outline: Optional[List[Dict]] = None):
        """Initialize with book outline context and Gemini configuration"""
        self.agent_config = agent_config
        self.outline = outline
        self.world_elements = {}
        self.character_developments = {}


        if (
            not agent_config
            or not agent_config.get("config_list")
            or not agent_config["config_list"][0]
        ):
            raise ValueError(
                "Invalid agent_config structure. Expected 'config_list' with at least one entry."
            )

        config = agent_config["config_list"][0]
        api_key = config.get("api_key")
        self.model_name = config.get(
            "model"
        )

        if not api_key:
            raise ValueError("Missing 'api_key' in agent_config")
        if not self.model_name:
            raise ValueError(
                "Missing 'model' name in agent_config (e.g., 'gemini-pro')"
            )

        # Configure the Gemini client
        genai.configure(api_key=api_key)

        # Initialize the Generative Model
        # Define safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        self.gemini_model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
        )

        # Store generation parameters
        self.temperature = agent_config.get("temperature", 0.7)

        # figuer out how to set this dynamically, or up it a whole lot for gemini 2.0 +
        self.max_output_tokens = agent_config.get("max_tokens", 8000)


    def _format_outline_context(self) -> str:
        """Format the book outline into a readable context (Unchanged)"""
        if not self.outline:
            return ""

        context_parts = ["Complete Book Outline:"]
        for chapter in self.outline:
            context_parts.extend(
                [
                    f"\nChapter {chapter['chapter_number']}: {chapter['title']}",
                    chapter["prompt"],
                ]
            )
        return "\n".join(context_parts)

    def create_agents(self, initial_prompt, num_chapters) -> Dict:
        """Set up system prompts for each agent type (Largely Unchanged)"""
        outline_context = self._format_outline_context()

        self.system_prompts = {
            # Keep all your existing prompt definitions here
            "memory_keeper": f"""You are the keeper of the story's continuity and context.
            ... (rest of prompt) ...""",
            "character_generator": f"""You are an expert character creator who designs rich, memorable characters.
            ... (rest of prompt) ...""",
            "story_planner": f"""You are an expert story arc planner focused on overall narrative structure.
            ... (rest of prompt) ...""",
            "outline_creator": f"""Generate a detailed {num_chapters}-chapter outline.
            ... (rest of prompt) ...""",
            "world_builder": f"""You are an expert in world-building who creates rich, consistent settings.
            ... (rest of prompt) ...""",
            "writer": f"""You are an expert creative writer who brings scenes to life.
            ... (rest of prompt) ...""",
            "editor": f"""You are an expert editor ensuring quality and consistency.
            ... (rest of prompt) ...""",
            "world_builder_chat": f"""You are a collaborative, creative world-building assistant helping an author develop a rich, detailed world for their book.
            ... (rest of prompt) ...""",
            "outline_creator_chat": f"""You are a collaborative, creative story development assistant helping an author brainstorm and develop their book outline.
            ... (rest of prompt) ...""",
        }

        return {}


    def _prepare_gemini_messages(
        self,
        agent_name: str,
        user_prompt: Optional[str] = None,
        history: Optional[List[Dict]] = None,
    ) -> List[Dict[str, str]]:
        """Prepares messages for Gemini API, prepending system prompt to the first user turn."""
        gemini_messages = []
        system_prompt = self.system_prompts.get(agent_name, "")

        if history:
            for i, entry in enumerate(history):
                role = "user" if entry["role"] == "user" else "model"
                content = entry["content"]
                # Prepend system prompt to the *first* user message in history
                if i == 0 and role == "user" and system_prompt:
                    content = f"{system_prompt}\n\n---\n\n{content}"
                gemini_messages.append(
                    {"role": role, "parts": [content]}
                )
            # Add the latest user message if provided
            if user_prompt:
                # If history was empty, prepend system prompt here
                if not gemini_messages and system_prompt:
                    gemini_messages.append(
                        {
                            "role": "user",
                            "parts": [f"{system_prompt}\n\n---\n\n{user_prompt}"],
                        }
                    )
                else:
                    gemini_messages.append({"role": "user", "parts": [user_prompt]})
        elif user_prompt:
            # Single turn generation: combine system and user prompt
            full_user_prompt = (
                f"{system_prompt}\n\n---\n\n{user_prompt}"
                if system_prompt
                else user_prompt
            )
            gemini_messages.append({"role": "user", "parts": [full_user_prompt]})
        elif system_prompt:
            # Case where only system prompt might be needed (less common for generate)
            gemini_messages.append({"role": "user", "parts": [system_prompt]})


        return gemini_messages

    def generate_content(self, agent_name: str, prompt: str) -> str:
        """Generate content using the Google Gemini API with the specified agent system prompt"""
        if agent_name not in self.system_prompts:
            raise ValueError(
                f"Agent '{agent_name}' not found. Available agents: {list(self.system_prompts.keys())}"
            )

        messages = self._prepare_gemini_messages(agent_name, user_prompt=prompt)

        if not messages:
            raise ValueError("Cannot generate content without a prompt.")

        # Define generation config
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature, max_output_tokens=self.max_output_tokens
        )

        try:
            response = self.gemini_model.generate_content(
                messages,  # Pass the prepared list
                generation_config=generation_config,
                # safety_settings can also be passed per-request if needed
            )

            # Check for safety blocks before accessing text
            if not response.candidates:
                finish_reason = (
                    response.prompt_feedback.block_reason
                    if response.prompt_feedback
                    else "Unknown"
                )
                # You might want to log response.prompt_feedback details here
                print(
                    f"WARN: Gemini content generation blocked or failed. Reason: {finish_reason}"
                )
                # Return a specific message or raise an error based on your needs
                return f"[Content Generation Blocked/Failed: {finish_reason}]"

            # Extract the response text
            generated_text = response.text

        except Exception as e:
            # Handle potential API errors (network, configuration, etc.)
            print(f"ERROR: Gemini API call failed for agent '{agent_name}': {e}")
            raise

        # Post-processing
        cleaned_response = generated_text  # Default to the full response

        if agent_name == "outline_creator":
            start = generated_text.find("OUTLINE:")
            end = generated_text.find("END OF OUTLINE")
            if start != -1:  # Find OUTLINE: regardless of END OF OUTLINE presence
                # Try to get content up to END OF OUTLINE if it exists
                if end != -1 and end > start:
                    cleaned_response = generated_text[
                        start : end + len("END OF OUTLINE")
                    ]
                else:  # Otherwise take everything from OUTLINE: onwards
                    cleaned_response = generated_text[start:]
                return cleaned_response.strip()  # Strip whitespace

        elif agent_name == "writer":
            if "SCENE FINAL:" in generated_text:
                parts = generated_text.split("SCENE FINAL:", 1)  # Split only once
                if len(parts) > 1:
                    cleaned_response = parts[1].strip()
                    return cleaned_response
            elif "SCENE:" in generated_text:  # Fallback if only SCENE: is present
                parts = generated_text.split("SCENE:", 1)
                if len(parts) > 1:
                    cleaned_response = parts[1].strip()
                    return cleaned_response

        elif agent_name == "world_builder":
            start = generated_text.find("WORLD_ELEMENTS:")
            if start != -1:
                cleaned_response = generated_text[start:].strip()
                return cleaned_response
            else:  # Fallback markers
                for marker in [
                    "Time Period",
                    "Setting:",
                    "Locations:",
                    "Major Locations",
                    "[LOCATION NAME]:",
                ]:
                    if marker in generated_text:
                        cleaned_response = (
                            generated_text
                        )
                        return cleaned_response

        elif agent_name == "story_planner":
            start = generated_text.find("STORY_ARC:")
            if start != -1:
                cleaned_response = generated_text[start:].strip()
                return cleaned_response

        elif agent_name == "character_generator":
            start = generated_text.find("CHARACTER_PROFILES:")
            if start != -1:
                cleaned_response = generated_text[start:].strip()
                return cleaned_response
            else:  # Fallback markers
                for marker in [
                    "Character 1:",
                    "Main Character:",
                    "Protagonist:",
                    "[CHARACTER NAME 1]:",
                ]:
                    if marker in generated_text:
                        cleaned_response = generated_text
                        return cleaned_response

        return cleaned_response


    def generate_chat_response(self, chat_history, topic, user_message) -> str:
        """Generate a chat response based on conversation history using Gemini."""
        agent_name = "world_builder_chat"
        if agent_name not in self.system_prompts:
            # Fallback or error if the default chat agent isn't defined
            raise ValueError(f"Default chat agent '{agent_name}' not found.")

        # Prepare messages for Gemini chat format
        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=user_message, history=chat_history
        )

        if not messages:
            return "[No input provided for chat]"

        # Define generation config
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature, max_output_tokens=self.max_output_tokens
        )

        try:
            # Call the Gemini API
            response = self.gemini_model.generate_content(
                messages,
                generation_config=generation_config,
            )

            if not response.candidates:
                finish_reason = (
                    response.prompt_feedback.block_reason
                    if response.prompt_feedback
                    else "Unknown"
                )
                print(
                    f"WARN: Gemini chat response blocked or failed. Reason: {finish_reason}"
                )
                return f"[Chat Response Blocked/Failed: {finish_reason}]"

            # Extract the response text
            return response.text

        except Exception as e:
            print(f"ERROR: Gemini chat API call failed: {e}")
            # Return an error message or raise
            return f"[ERROR: Could not generate chat response - {e}]"


    def generate_chat_response_stream(
        self, chat_history, topic, user_message
    ) -> Iterable:
        """Generate a streaming chat response based on conversation history using Gemini."""
        agent_name = "world_builder_chat"
        if agent_name not in self.system_prompts:
            raise ValueError(f"Default chat agent '{agent_name}' not found.")

        # Prepare messages for Gemini chat format
        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=user_message, history=chat_history
        )

        if not messages:
            # Return an empty generator or handle as needed
            def empty_generator():
                yield "[No input provided for stream]"

            return empty_generator()

        # Define generation config
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,  # Max tokens applies to the whole response
        )

        try:
            # Call the API with streaming enabled
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            # Return the stream iterator directly
            # The caller will iterate through chunks (e.g., for chunk in stream: yield chunk.text)
            return stream

        except Exception as e:
            print(f"ERROR: Gemini streaming chat API call failed: {e}")

            # Return a generator yielding an error or raise
            def error_generator():
                yield f"[ERROR: Could not generate streaming chat response - {e}]"

            return error_generator()

    def generate_final_world(self, chat_history, topic) -> str:
        """Generate final world setting based on chat history using Gemini."""

        final_world_system_prompt = """You are an expert world-building specialist.
        Based on the entire conversation provided (history of user and assistant messages), create a comprehensive, well-structured world setting document.

        Format your response clearly, potentially using sections like:
        WORLD_ELEMENTS:

        1. Time period and setting: [detailed description]
        2. Major locations: [detailed description of each key location]
        3. Cultural/historical elements: [key cultural and historical aspects]
        4. Technology/magical elements: [if applicable]
        5. Social/political structures: [governments, factions, etc.]
        6. Environment and atmosphere: [natural world aspects]

        Make this a complete, cohesive reference document that covers all important aspects of the world mentioned in the conversation. Add necessary details to fill any gaps, while staying true to everything established in the chat history."""

        # Add a final instruction to the user prompt part of the messages
        final_instruction = f"Please create the final, comprehensive world setting document for my book about '{topic}' based on our entire conversation history."

        # Prepare messages - use the specific system prompt and the history + final instruction
        gemini_messages = []
        # Add the specific system prompt implicitly by prepending to the first *effective* user turn
        first_user_message_content = ""
        history_turns = []

        # Process history into Gemini format
        for i, entry in enumerate(chat_history):
            role = "user" if entry["role"] == "user" else "model"
            content = entry["content"]
            if i == 0 and role == "user":  # Prepare to prepend system prompt
                first_user_message_content = content
            else:
                history_turns.append({"role": role, "parts": [content]})

        # Construct the first turn, prepending system prompt
        if first_user_message_content:
            gemini_messages.append(
                {
                    "role": "user",
                    "parts": [
                        f"{final_world_system_prompt}\n\n---\n\n{first_user_message_content}"
                    ],
                }
            )
            gemini_messages.extend(history_turns)  # Add rest of history
        elif history_turns:  # If history started with 'assistant'
            print(
                "WARN: Chat history doesn't start with user. System prompt might not be ideally placed."
            )
            gemini_messages.extend(history_turns)  # Add history as is

        # Add the final instruction as the last user message
        if not gemini_messages:  # If history was empty
            gemini_messages.append(
                {
                    "role": "user",
                    "parts": [
                        f"{final_world_system_prompt}\n\n---\n\n{final_instruction}"
                    ],
                }
            )
        else:
            gemini_messages.append({"role": "user", "parts": [final_instruction]})

        if not gemini_messages:
            return "[Cannot generate final world without history or instruction]"

        # Define generation config
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )

        try:
            response = self.gemini_model.generate_content(
                gemini_messages,
                generation_config=generation_config,
            )

            if not response.candidates:
                finish_reason = (
                    response.prompt_feedback.block_reason
                    if response.prompt_feedback
                    else "Unknown"
                )
                print(
                    f"WARN: Gemini final world generation blocked or failed. Reason: {finish_reason}"
                )
                return f"[Final World Generation Blocked/Failed: {finish_reason}]"

            generated_text = response.text
            # Ensure it has the WORLD_ELEMENTS header for consistency
            if "WORLD_ELEMENTS:" not in generated_text:
                generated_text = "WORLD_ELEMENTS:\n\n" + generated_text
            return generated_text

        except Exception as e:
            print(f"ERROR: Gemini final world generation failed: {e}")
            return f"[ERROR: Could not generate final world - {e}]"

    def generate_final_world_stream(self, chat_history, topic) -> Iterable:
        """Generate the final world setting based on the chat history using streaming Gemini."""
        # Use the world_builder system prompt (or a dedicated finalization prompt)
        agent_name = "world_builder"  # Or reuse the specific final prompt from above
        final_instruction = f"Based on our conversation about '{topic}', please create a comprehensive and detailed world setting. Format it with clear sections for different aspects of the world (geography, magic/technology, culture, etc.). This will be the final world setting for the book."

        # Prepare messages
        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=final_instruction, history=chat_history
        )

        if not messages:

            def empty_generator():
                yield "[No input provided for final world stream]"

            return empty_generator()

        # Define generation config
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,  # Adjust as needed
            max_output_tokens=self.max_output_tokens,
        )

        try:
            # Call the API with streaming enabled
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            return stream  # Return the iterator

        except Exception as e:
            print(f"ERROR: Gemini final world streaming API call failed: {e}")

            def error_generator():
                yield f"[ERROR: Could not generate final world stream - {e}]"

            return error_generator()

    # =====================================================

    # --- Unchanged methods (no direct LLM calls) ---
    def update_world_element(self, element_name: str, description: str) -> None:
        """Update a world element description"""
        self.world_elements[element_name] = description

    def update_character_development(
        self, character_name: str, development: str
    ) -> None:
        """Update a character's development"""
        if character_name not in self.character_developments:
            self.character_developments[character_name] = []
        self.character_developments[character_name].append(development)

    def get_world_context(self) -> str:
        """Get a formatted string of all world elements"""
        if not self.world_elements:
            return ""
        elements = ["WORLD ELEMENTS:"]
        for name, desc in self.world_elements.items():
            elements.append(f"\n{name}:\n{desc}")
        return "\n".join(elements)

    def get_character_context(self) -> str:
        """Get a formatted string of all character developments"""
        if not self.character_developments:
            return ""
        developments = ["CHARACTER DEVELOPMENTS:"]
        for name, devs in self.character_developments.items():
            developments.append(f"\n{name}:")
            for i, dev in enumerate(devs, 1):
                developments.append(f"{i}. {dev}")
        return "\n".join(developments)

    # --------------------------------------------

    # === REVISED: Character generation methods using Gemini ===
    # (Showing stream version - non-stream is similar, just call generate_content without stream=True)
    def generate_chat_response_characters_stream(
        self, chat_history, world_theme, user_message
    ) -> Iterable:
        """Generate a streaming chat response about character creation using Gemini."""
        agent_name = "character_generator"  # Use the specific agent prompt

        # We need to provide the world theme as context. Gemini doesn't have a separate 'system' context mechanism
        # like OpenAI API v1 for some models. We inject it into the effective system prompt.
        base_system_prompt = self.system_prompts.get(agent_name, "")
        contextual_system_prompt = f"{base_system_prompt}\n\nCONTEXT:\nThe book takes place in the following world:\n{world_theme}\n---"

        # Prepare messages, using the enhanced system prompt
        # Create a temporary modified system_prompts dict or pass prompt directly
        temp_system_prompts = self.system_prompts.copy()
        temp_system_prompts[agent_name] = contextual_system_prompt

        original_prompts = self.system_prompts  # Backup
        self.system_prompts = temp_system_prompts  # Temporarily override

        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=user_message, history=chat_history
        )

        self.system_prompts = original_prompts  # Restore

        if not messages:

            def empty_generator():
                yield "[No input for character chat stream]"
                return empty_generator()

        generation_config = genai.types.GenerationConfig(
            temperature=0.7, max_output_tokens=self.max_output_tokens
        )

        try:
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            return stream
        except Exception as e:
            print(f"ERROR: Gemini character chat streaming failed: {e}")

            def error_generator():
                yield f"[ERROR: Character chat stream failed - {e}]"
                return error_generator()

    # =======================================================

    # === REVISED: Final character generation (stream) ===
    def generate_final_characters_stream(
        self, chat_history, world_theme, num_characters=3
    ) -> Iterable:
        """Generate the final character profiles based on chat history using streaming Gemini."""
        agent_name = "character_generator"
        final_instruction = f"Based on our conversation, please create {num_characters} detailed character profiles for the book. Format each character with Name, Role, Physical Description, Background, Personality, and Goals/Motivations, following the format specified in your initial instructions. This will be the final character list for the book."

        # Inject world theme context into system prompt
        base_system_prompt = self.system_prompts.get(agent_name, "")
        contextual_system_prompt = f"{base_system_prompt}\n\nCONTEXT:\nThe book takes place in the following world:\n{world_theme}\n---"

        # Prepare messages using modified system prompt
        temp_system_prompts = self.system_prompts.copy()
        temp_system_prompts[agent_name] = contextual_system_prompt
        original_prompts = self.system_prompts
        self.system_prompts = temp_system_prompts

        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=final_instruction, history=chat_history
        )

        self.system_prompts = original_prompts  # Restore

        if not messages:

            def empty_generator():
                yield "[No input for final characters stream]"
                return empty_generator()

        generation_config = genai.types.GenerationConfig(
            temperature=0.7, max_output_tokens=self.max_output_tokens
        )

        try:
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            return stream
        except Exception as e:
            print(f"ERROR: Gemini final characters streaming failed: {e}")

            def error_generator():
                yield f"[ERROR: Final characters stream failed - {e}]"
                return error_generator()

    # ===================================================

    # === REVISED: Outline generation methods using Gemini ===
    # (Showing stream version - non-stream is similar)
    def generate_chat_response_outline_stream(
        self, chat_history, world_theme, characters, user_message
    ) -> Iterable:
        """Generate a streaming chat response about outline creation using Gemini."""
        agent_name = "outline_creator_chat"  # Use the brainstorming chat prompt

        # Inject world and character context into system prompt
        base_system_prompt = self.system_prompts.get(agent_name, "")
        contextual_system_prompt = f"{base_system_prompt}\n\nCONTEXT:\nThe book takes place in the following world:\n{world_theme}\n\nThe characters include:\n{characters}\n---"

        # Prepare messages using modified system prompt
        temp_system_prompts = self.system_prompts.copy()
        temp_system_prompts[agent_name] = contextual_system_prompt
        original_prompts = self.system_prompts
        self.system_prompts = temp_system_prompts

        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=user_message, history=chat_history
        )

        self.system_prompts = original_prompts  # Restore

        if not messages:

            def empty_generator():
                yield "[No input for outline chat stream]"
                return empty_generator()

        generation_config = genai.types.GenerationConfig(
            temperature=0.7, max_output_tokens=self.max_output_tokens
        )

        try:
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            return stream
        except Exception as e:
            print(f"ERROR: Gemini outline chat streaming failed: {e}")

            def error_generator():
                yield f"[ERROR: Outline chat stream failed - {e}]"
                return error_generator()

    # ====================================================

    # === REVISED: Final outline generation (stream) ===
    def generate_final_outline_stream(
        self, chat_history, world_theme, characters, num_chapters=10
    ) -> Iterable:
        """Generate the final outline based on chat history using streaming Gemini."""
        agent_name = "outline_creator"  # Use the final outline generator prompt
        final_instruction = f"""Based on our conversation, please create a detailed {num_chapters}-chapter outline for the book.

CRITICAL REQUIREMENTS:
1. Create EXACTLY {num_chapters} chapters, numbered sequentially from 1 to {num_chapters}
2. NEVER repeat chapter numbers or restart the numbering
3. Follow the exact format specified in your initial instructions (OUTLINE:, Chapter X:, - Key Events:, etc.)
4. Each chapter must have a unique title and AT LEAST 3 specific Key Events
5. Maintain a coherent story from beginning to end

Format it as a properly structured outline with clear chapter sections and events. This will be the final outline for the book."""

        # Inject world and character context into system prompt
        base_system_prompt = self.system_prompts.get(agent_name, "").format(
            num_chapters=num_chapters
        )  # Format num_chapters if needed
        contextual_system_prompt = f"{base_system_prompt}\n\nCONTEXT:\nThe book takes place in the following world:\n{world_theme}\n\nThe characters include:\n{characters}\n---"

        # Prepare messages using modified system prompt
        temp_system_prompts = self.system_prompts.copy()
        temp_system_prompts[agent_name] = contextual_system_prompt
        original_prompts = self.system_prompts
        self.system_prompts = temp_system_prompts

        messages = self._prepare_gemini_messages(
            agent_name, user_prompt=final_instruction, history=chat_history
        )

        self.system_prompts = original_prompts  # Restore

        if not messages:

            def empty_generator():
                yield "[No input for final outline stream]"
                return empty_generator()

        # Slightly lower temperature for more structured output might be good here
        generation_config = genai.types.GenerationConfig(
            temperature=0.6, max_output_tokens=self.max_output_tokens
        )

        try:
            stream = self.gemini_model.generate_content(
                messages, generation_config=generation_config, stream=True
            )
            return stream
        except Exception as e:
            print(f"ERROR: Gemini final outline streaming failed: {e}")

            def error_generator():
                yield f"[ERROR: Final outline stream failed - {e}]"
                return error_generator()

    # ================================================
