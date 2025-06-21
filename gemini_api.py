import logging
import time
from datetime import timedelta
from config import config

class GeminiAPI:
    """Google Gemini AI integration for generating task descriptions"""
    
    def __init__(self):
        self.api_key = config.gemini_api_key
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client with automatic best model selection"""
        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
                
                # Get the best available model automatically
                best_model = self._get_best_model(genai)
                if best_model:
                    try:
                        self.model = genai.GenerativeModel(best_model)
                        # Test the model with a simple query
                        test_response = self.model.generate_content("Hello")
                        if test_response and test_response.text:
                            logging.info(f"Successfully initialized Gemini with best model: {best_model}")
                            return True
                    except Exception as e:
                        logging.error(f"Failed to initialize best model {best_model}: {e}")
                
                # Fallback to manual selection if auto-detection fails
                return self._fallback_model_selection(genai)
                
        except ImportError:
            logging.warning("google-generativeai package not installed")
        except Exception as e:
            logging.error(f"Error initializing Gemini: {e}")
        return False
    
    def _get_best_model(self, genai):
        """Automatically select the best available model"""
        try:
            models = genai.list_models()
            available_models = []
            
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append({
                        'name': model.name,
                        'display_name': getattr(model, 'display_name', model.name),
                        'description': getattr(model, 'description', '')
                    })
            
            if not available_models:
                return None
            
            # Priority ranking for model selection (higher score = better)
            def score_model(model):
                name = model['name'].lower()
                score = 0
                
                # Prioritize thinking models (highest priority)
                if 'thinking' in name:
                    score += 10000  # Massive bonus for thinking models
                
                # Dynamic version scoring - future-proof for newer versions
                version_score = self._extract_version_score(name)
                score += version_score
                
                # Model type preferences
                if 'pro' in name:
                    score += 400  # Pro models are more capable
                elif 'flash' in name:
                    score += 300  # Flash models are fast and efficient
                
                # Experimental models get bonus points (often newest features)
                if 'exp' in name or 'experimental' in name:
                    score += 200
                
                # Ultra or advanced variants
                if 'ultra' in name:
                    score += 500
                elif 'advanced' in name:
                    score += 350
                
                return score
            
            # Sort models by score (highest first)
            ranked_models = sorted(available_models, key=score_model, reverse=True)
            
            # Log the selection process
            logging.info("Available models ranked by preference:")
            for i, model in enumerate(ranked_models[:5]):  # Show top 5
                logging.info(f"  {i+1}. {model['name']} (score: {score_model(model)})")
            
            return ranked_models[0]['name']
            
        except Exception as e:
            logging.error(f"Error getting best model: {e}")
            return None
    
    def _extract_version_score(self, model_name):
        """Extract version number and calculate score dynamically"""
        import re
        
        # Look for version patterns like 1.0, 1.5, 2.0, 2.5, 3.0, etc.
        version_pattern = r'(\d+)\.(\d+)'
        match = re.search(version_pattern, model_name)
        
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            
            # Dynamic scoring: major version * 1000 + minor version * 100
            # This ensures 3.0 > 2.5 > 2.0 > 1.5 > 1.0
            version_score = major * 1000 + minor * 100
            
            # Bonus for very new versions (4.0+, 5.0+, etc.)
            if major >= 4:
                version_score += 500  # Future-proofing bonus
            elif major >= 3:
                version_score += 200  # Next-gen bonus
            
            return version_score
        
        # If no version found, check for legacy patterns
        if 'pro' in model_name and 'gemini-pro' == model_name:
            return 100  # Legacy gemini-pro (assumed 1.0)
        
        return 0  # No version information
    
    def _fallback_model_selection(self, genai):
        """Fallback to manual model selection if auto-detection fails"""
        # Dynamic fallback list - prioritizing thinking models and newer versions
        fallback_models = [
            # Thinking models (highest priority) - future versions
            'gemini-3.0-flash-thinking-exp',
            'gemini-2.5-flash-thinking-exp', 
            'gemini-2.0-flash-thinking-exp',
            'gemini-1.5-pro-thinking-exp',
            
            # Latest non-thinking models
            'gemini-3.0-ultra',
            'gemini-3.0-pro',
            'gemini-3.0-flash',
            'gemini-2.5-ultra',
            'gemini-2.5-pro',
            'gemini-2.5-flash',
            'gemini-2.0-ultra-exp',
            'gemini-2.0-pro-exp',
            'gemini-2.0-flash-exp',
            
            # Current stable models
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            
            # Legacy fallback
            'gemini-pro'
        ]
        
        for model_name in fallback_models:
            try:
                self.model = genai.GenerativeModel(model_name)
                test_response = self.model.generate_content("Hello")
                if test_response and test_response.text:
                    logging.info(f"Fallback: Successfully initialized with {model_name}")
                    return True
            except Exception as e:
                logging.debug(f"Fallback failed for model {model_name}: {e}")
                continue
        
        logging.error("All fallback models failed")
        return False
    
    def test_connection(self):
        """Test Gemini API connection and report model details"""
        if not self.model:
            return False, "Gemini client not initialized. Check API key and dependencies."
        
        try:
            response = self.model.generate_content("Hello, this is a test.")
            if response and response.text:
                # Get model info if available
                model_name = getattr(self.model, '_model_name', 'Unknown model')
                return True, f"Gemini API connected successfully using {model_name}"
            else:
                return False, "Gemini API responded but with empty content"
        except Exception as e:
            return False, f"Gemini API Error: {str(e)}"
    
    def get_model_info(self):
        """Get information about the currently selected model"""
        if not self.model:
            return None
        
        try:
            import google.generativeai as genai
            models = genai.list_models()
            
            current_model_name = getattr(self.model, '_model_name', None)
            if not current_model_name:
                return {"name": "Unknown", "capabilities": "Unknown"}
            
            for model in models:
                if model.name == current_model_name:
                    return {
                        "name": model.name,
                        "display_name": getattr(model, 'display_name', model.name),
                        "description": getattr(model, 'description', 'No description'),
                        "supported_methods": getattr(model, 'supported_generation_methods', []),
                        "input_token_limit": getattr(model, 'input_token_limit', 'Unknown'),
                        "output_token_limit": getattr(model, 'output_token_limit', 'Unknown')
                    }
            
            return {"name": current_model_name, "capabilities": "Model details not found"}
            
        except Exception as e:
            return {"name": "Unknown", "error": str(e)}
    
    def generate_task_list(self, commits_data, user_preferences=None, max_retries=3):
        """Generate task list from GitHub commits with retry logic"""
        if not self.model:
            return False, "Gemini client not initialized"
        
        for attempt in range(max_retries):
            try:
                # Build prompt
                prompt = self._build_task_prompt(commits_data, user_preferences)
                
                # Add delay between retries to help with rate limiting
                if attempt > 0:
                    delay = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    print(f"🔄 Retrying AI generation (attempt {attempt + 1}/{max_retries}) in {delay}s...")
                    time.sleep(delay)
                
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return True, response.text
                else:
                    logging.warning(f"Attempt {attempt + 1}: Gemini returned empty response")
                    
            except Exception as e:
                error_msg = str(e)
                logging.warning(f"Attempt {attempt + 1}: AI generation failed: {error_msg}")
                
                # Check if it's a retryable error
                if "500" in error_msg or "internal error" in error_msg.lower() or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        continue  # Retry for server errors or quota issues
                else:
                    # Non-retryable error, fail immediately
                    return False, f"Error generating tasks: {error_msg}"
        
        # All retries exhausted
        return False, f"Failed to generate tasks after {max_retries} attempts. Gemini API may be experiencing issues."
    
    def _build_task_prompt(self, commits_data, user_preferences=None):
        """Build a concise but effective prompt for time tracking generation"""
        working_hours = user_preferences.get('daily_hours', 7) if user_preferences else 7
        working_days = user_preferences.get('days_per_week', 5) if user_preferences else 5
        weekly_hours = working_hours * working_days
        start_date = user_preferences.get('start_date') if user_preferences else None
        end_date = user_preferences.get('end_date') if user_preferences else None
        
        # Calculate total expected hours more safely
        total_expected_hours = "calculated automatically"
        try:
            if start_date and end_date:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                work_days = 0
                current = start_dt
                while current <= end_dt:
                    if current.weekday() < 5:  # Monday=0, Friday=4
                        work_days += 1
                    current += timedelta(days=1)
                total_expected_hours = work_days * working_hours
        except Exception:
            total_expected_hours = f"~{weekly_hours * 4}"
        
        prompt = f"""Create a complete work schedule covering ALL hours evenly.

REQUIREMENTS:
- {working_hours} hours per day, {working_days} days per week
- Period: {start_date} to {end_date}
- Target total: {total_expected_hours} hours
- Each week must have exactly {weekly_hours} hours

WEEKLY MEETINGS:"""
        
        # Add meeting information concisely
        meetings = user_preferences.get('meetings', []) if user_preferences else []
        if meetings:
            prompt += "\nInclude these meetings EVERY week:\n"
            for meeting in meetings[:3]:  # Limit to 3 meetings to keep prompt manageable
                prompt += f"- {meeting['day']} {meeting['start_time']}-{meeting['end_time']}: {meeting['description']}\n"
        else:
            prompt += "\nNo fixed meetings.\n"
        
        prompt += f"""
COMMITS TO BASE TASKS ON:
"""
        # Limit commits to prevent prompt from being too large
        for i, commit in enumerate(commits_data[:20]):  # Reduced from 50 to 20
            prompt += f"{i+1}. {commit['date'][:10]} - {commit['message'][:80]}...\n"
        
        prompt += f"""
OUTPUT FORMAT (CSV only):
date,start,end,description,projectName,taskName,billable

RULES:
1. Every day = exactly {working_hours} hours
2. Every week = exactly {weekly_hours} hours  
3. Include fixed meetings at specified times
4. Distribute remaining time across development tasks
5. Use commits as basis for task descriptions
6. Fill any gaps with code review, testing, documentation

Return ONLY CSV data, no other text."""
        
        return prompt
    
    def get_api_key_help(self):
        """Provide help for getting Gemini API key"""
        return """
To get a Google Gemini API key:
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API key"
3. Choose "Create API key in new project" or select existing project
4. Copy the generated API key
5. Add it to your _API_KEYS file as GEMINI_API_KEY=your_api_key_here

Note: You may need to enable the Generative AI API in Google Cloud Console.
"""