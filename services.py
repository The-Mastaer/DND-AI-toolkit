import logging
from google import genai
import json
from supabase import create_client, Client
import io


class DataManager:
    """
    Manages all database operations for the DM's AI Toolkit.
    This version is refactored to use Supabase (PostgreSQL).
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logging.info("Supabase client initialized successfully.")
        else:
            self.supabase: Client = None
            logging.error("Supabase URL or Key not provided. DataManager is non-functional.")

    def _check_client(self):
        if not self.supabase:
            raise ConnectionError("Supabase client is not configured. Check your credentials.")
        return True

    # --- World Management ---
    def create_world(self, name, language, lore=""):
        self._check_client()
        canonical_name = f"{name.lower().replace(' ', '_')}"
        try:
            world_response = self.supabase.table('worlds').insert({"canonical_name": canonical_name}).execute()
            if not world_response.data: raise Exception(
                f"Failed to create world: {world_response.error.message if world_response.error else 'No data returned'}")
            world_id = world_response.data[0]['world_id']
            trans_response = self.supabase.table('world_translations').insert(
                {"world_id": world_id, "language": language, "world_name": name, "world_lore": lore}).execute()
            if not trans_response.data:
                self.supabase.table('worlds').delete().eq('world_id', world_id).execute()
                raise Exception(
                    f"Failed to create world translation: {trans_response.error.message if trans_response.error else 'No data returned'}")
            logging.info(f"Successfully created world '{name}' (ID: {world_id}) with '{language}' translation.")
            return world_id
        except Exception as e:
            logging.error(f"Database error while creating world '{name}': {e}")
            raise

    def get_all_worlds(self, language):
        self._check_client()
        try:
            response = self.supabase.table('v_full_world_data').select('*').eq('language', language).order(
                'world_name').execute()
            return response.data if response.data else []
        except Exception as e:
            logging.error(f"Failed to load worlds from database: {e}")
            return []

    def get_world_translation(self, world_id, language):
        self._check_client()
        try:
            response = self.supabase.table('v_full_world_data').select('*').eq('world_id', world_id).eq('language',
                                                                                                        language).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Failed to get translation for world {world_id} in '{language}': {e}")
            return None

    def update_world_translation(self, world_id, language, name, lore):
        self._check_client()
        try:
            self.supabase.table('world_translations').upsert(
                {"world_id": world_id, "language": language, "world_name": name, "world_lore": lore},
                on_conflict='world_id, language').execute()
            logging.info(f"Successfully updated translation for world ID {world_id} in '{language}'.")
        except Exception as e:
            logging.error(f"Failed to update world translation for world ID {world_id}: {e}")
            raise

    def delete_world(self, world_id):
        self._check_client()
        try:
            self.supabase.table('worlds').delete().eq('world_id', world_id).execute()
            logging.info(f"Successfully deleted world ID: {world_id}")
        except Exception as e:
            logging.error(f"Failed to delete world ID {world_id}: {e}")
            raise

    # --- Campaign Management ---
    def create_campaign(self, world_id, name, language, party_info="", session_history=""):
        self._check_client()
        try:
            response = self.supabase.table('campaigns').insert(
                {"world_id": world_id, "campaign_name": name, "language": language, "party_info": party_info,
                 "session_history": session_history}).execute()
            logging.info(f"Successfully created campaign '{name}' in world ID {world_id}.")
            return response.data[0]['campaign_id']
        except Exception as e:
            logging.error(f"Database error while creating campaign '{name}': {e}")
            raise

    def get_campaigns_for_world(self, world_id):
        self._check_client()
        try:
            response = self.supabase.table('campaigns').select('*').eq('world_id', world_id).order(
                'campaign_name').execute()
            return response.data
        except Exception as e:
            logging.error(f"Failed to load campaigns for world ID {world_id}: {e}")
            return []

    def update_campaign(self, campaign_id, name, language, party_info, session_history):
        self._check_client()
        try:
            self.supabase.table('campaigns').update(
                {"campaign_name": name, "language": language, "party_info": party_info,
                 "session_history": session_history}).eq('campaign_id', campaign_id).execute()
            logging.info(f"Successfully updated campaign ID: {campaign_id}")
        except Exception as e:
            logging.error(f"Failed to update campaign ID {campaign_id}: {e}")
            raise

    def delete_campaign(self, campaign_id):
        self._check_client()
        try:
            self.supabase.table('campaigns').delete().eq('campaign_id', campaign_id).execute()
            logging.info(f"Successfully deleted campaign ID: {campaign_id}")
        except Exception as e:
            logging.error(f"Failed to delete campaign ID {campaign_id}: {e}")
            raise

    # --- Character Management ---
    def create_character(self, world_id, is_player, language, core_data, translation_data):
        self._check_client()
        try:
            core_data['world_id'] = world_id
            core_data['is_player'] = is_player
            core_response = self.supabase.table('characters').insert(core_data).execute()
            if not core_response.data: raise Exception(
                f"Failed to create character core: {core_response.error.message if core_response.error else 'No data returned'}")
            character_id = core_response.data[0]['character_id']
            translation_data['character_id'] = character_id
            translation_data['language'] = language
            trans_response = self.supabase.table('character_translations').insert(translation_data).execute()
            if not trans_response.data:
                self.supabase.table('characters').delete().eq('character_id', character_id).execute()
                raise Exception(
                    f"Failed to create character translation: {trans_response.error.message if trans_response.error else 'No data returned'}")
            logging.info(f"Successfully created character ID {character_id} with '{language}' translation.")
            return character_id
        except Exception as e:
            logging.error(f"Database error while creating character: {e}")
            raise

    def get_characters_for_world(self, world_id, language):
        self._check_client()
        try:
            response = self.supabase.table('v_full_character_data').select('*').eq('world_id', world_id).eq('language',
                                                                                                            language).order(
                'name').execute()
            return response.data
        except Exception as e:
            logging.error(f"Failed to load characters for world ID {world_id}: {e}")
            return []

    def update_character(self, character_id, language, core_data, translation_data):
        self._check_client()
        try:
            self.supabase.table('characters').update(core_data).eq('character_id', character_id).execute()
            translation_data['character_id'] = character_id
            translation_data['language'] = language
            self.supabase.table('character_translations').upsert(translation_data,
                                                                 on_conflict='character_id, language').execute()
            logging.info(f"Successfully updated character ID {character_id} for language '{language}'.")
        except Exception as e:
            logging.error(f"Database error while updating character {character_id}: {e}")
            raise

    def delete_character(self, character_id):
        self._check_client()
        try:
            self.supabase.table('characters').delete().eq('character_id', character_id).execute()
            logging.info(f"Successfully deleted character ID: {character_id}")
        except Exception as e:
            logging.error(f"Failed to delete character ID {character_id}: {e}")
            raise

    # --- File Storage Management ---
    def upload_file(self, bucket_name: str, file_path: str, file_body: bytes):
        self._check_client()
        try:
            file_obj = io.BytesIO(file_body)
            file_obj.name = file_path
            self.supabase.storage.from_(bucket_name).upload(file=file_obj, path=file_path,
                                                            file_options={"cache-control": "3600", "upsert": "true"})
            public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)
            logging.info(f"File uploaded to {bucket_name}/{file_path}. Public URL: {public_url}")
            return public_url
        except Exception as e:
            logging.error(f"Failed to upload file to Supabase Storage: {e}")
            if hasattr(e, 'message'): logging.error(f"Supabase error message: {e.message}")
            raise


class GeminiService:
    """
    Manages all interactions with the Google Gemini API using the new google-genai SDK.
    """

    def __init__(self, api_key, app_settings, data_manager):
        self.api_key = api_key
        self.settings = app_settings
        self.db = data_manager
        self.client = None
        self.chat_sessions = {}
        self.srd_pdf_cache = None
        self._configure_api()

    def _configure_api(self):
        if self.is_api_key_valid():
            try:
                self.client = genai.Client(api_key=self.api_key)
                logging.info("Gemini API Client initialized successfully with the new SDK.")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini Client: {e}")
        else:
            logging.warning("API Key is missing or invalid. GeminiService is non-functional.")

    def is_api_key_valid(self):
        return self.api_key and "INSERT" not in self.api_key and len(self.api_key) > 10

    def get_or_start_chat_session(self, persona):
        if persona not in self.chat_sessions:
            if not self.client: return None
            text_model_name = self.settings.get("text_model")
            # With the new SDK, the model is part of the generate_content call,
            # but we can pre-start a chat session for context management.
            model = self.client.generative_model(text_model_name)
            self.chat_sessions[persona] = model.start_chat()
            logging.info(f"New chat session started for '{persona}' with model '{text_model_name}'.")
        return self.chat_sessions[persona]

    def clear_chat_session(self, persona):
        if persona in self.chat_sessions:
            del self.chat_sessions[persona]
            logging.info(f"Chat history for '{persona}' cleared.")

    def send_chat_message(self, user_prompt, persona):
        if not self.client: raise ConnectionError("Gemini Client not initialized.")
        if persona == "rules_lawyer": return self._handle_rules_lawyer_query(user_prompt)

        chat_session = self.get_or_start_chat_session(persona)
        if not chat_session: raise ConnectionError("Chat session not initialized.")

        full_prompt = self._build_prompt_with_context(user_prompt, persona)
        response = chat_session.send_message(full_prompt)
        return response.text

    def _build_prompt_with_context(self, user_prompt, persona):
        if persona == "lore_master":
            world_id = self.settings.get("active_world_id")
            campaign_id = self.settings.get("active_campaign_id")
            lang = self.settings.get("active_language")
            world_lore, party_info, session_history = "", "", ""
            if world_id:
                world_trans = self.db.get_world_translation(world_id, lang)
                if world_trans: world_lore = world_trans.get('world_lore', '')
            if campaign_id:
                all_campaigns = self.db.get_campaigns_for_world(world_id)
                campaign = next((c for c in all_campaigns if c['campaign_id'] == campaign_id), None)
                if campaign:
                    party_info = campaign.get('party_info', '')
                    session_history = campaign.get('session_history', '')
            prompt_template = self.settings.get("prompts", {}).get("lore_master")
            return prompt_template.format(world_lore=world_lore, party_info=party_info, session_history=session_history,
                                          user_question=user_prompt)
        return user_prompt

    def generate_npc(self, params, campaign_data=None, include_party=True, include_session=True):
        if not self.client: raise ValueError("API Client not configured.")
        campaign_data = campaign_data or {}
        text_model_name = self.settings.get("text_model")

        npc_generation_prompt_template = self.settings.get("prompts", {}).get("npc_generation")
        world_lore = ""
        if campaign_data and campaign_data.get('world_id'):
            world_trans = self.db.get_world_translation(campaign_data['world_id'], campaign_data['language'])
            if world_trans: world_lore = world_trans.get('world_lore', '')
        party_context = campaign_data.get('party_info', '') if include_party else ""
        session_context = campaign_data.get('session_history', '') if include_session else ""
        custom_prompt_text = params.get('custom_prompt', '')
        campaign_context_section = f"\n**Campaign Lore (Follow this lore closely):**\n{world_lore}\n" if world_lore else ""
        party_context_section = f"\n**Player Party Information (Consider their impact):**\n{party_context}\n" if party_context else ""
        session_context_section = f"\n**Recent Session History (The NPC may be aware of these events):**\n{session_context}\n" if session_context else ""
        custom_prompt_section = f"\n**Additional Custom Prompt:**\n- {custom_prompt_text}\n" if custom_prompt_text else ""
        prompt = npc_generation_prompt_template.format(
            gender=params['gender'], attitude=params['attitude'], rarity=params['rarity'],
            environment=params['environment'], race=params['race'], character_class=params['character_class'],
            background=params['background'],
            campaign_context=campaign_context_section,
            party_context=party_context_section,
            session_context=session_context_section,
            custom_prompt_section=custom_prompt_section
        )
        logging.info(f"Sending generation request to model '{text_model_name}'.")

        response = self.client.generate_content(
            model=f"models/{text_model_name}",
            contents=prompt,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
        )
        raw_text = response.text
        try:
            return json.loads(raw_text), raw_text
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from AI response. Raw text: {raw_text}\nError: {e}")
            raise ValueError(
                f"The AI returned a malformed description. Please try generating again. Details: {e}") from e

    def _handle_rules_lawyer_query(self, user_prompt):
        logging.warning("Rules Lawyer with local PDF not yet implemented in web version.")
        return "The Rules Lawyer feature using local PDFs is not yet available in this version of the application."