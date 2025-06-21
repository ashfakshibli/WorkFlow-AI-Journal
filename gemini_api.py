import logging
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
    
    def generate_task_list(self, commits_data, user_preferences=None):
        """Generate task list from GitHub commits"""
        if not self.model:
            return False, "Gemini client not initialized"
        
        try:
            # Build prompt
            prompt = self._build_task_prompt(commits_data, user_preferences)
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                return True, response.text
            else:
                return False, "Gemini returned empty response"
        except Exception as e:
            return False, f"Error generating tasks: {str(e)}"
    
    def _build_task_prompt(self, commits_data, user_preferences=None):
        """Build prompt for task generation"""
        working_hours = user_preferences.get('daily_hours', 8) if user_preferences else 8
        meetings_per_week = user_preferences.get('meetings_per_week', 2) if user_preferences else 2
        
        prompt = f"""
Based on the following GitHub commits, create a detailed task list in CSV format suitable for time tracking in Clockify.

Working parameters:
- Daily working hours: {working_hours} hours
- Weekly meetings: {meetings_per_week} meetings (30-40 minutes each)
- Estimate realistic time for each development task

GitHub Commits:
"""
        for i, commit in enumerate(commits_data[:20]):  # Limit to 20 commits
            prompt += f"{i+1}. {commit['date']} - {commit['message']} (by {commit['author']})\n"
        
        prompt += """

Please generate a CSV with the following columns:
date,start,end,description,projectName,taskName,billable

Guidelines:
- Break down commits into logical development tasks
- Estimate appropriate time for each task (coding usually takes 2-4 hours, testing 1-2 hours, etc.)
- Include code reviews, testing, and documentation time
- Use format: date (YYYY-MM-DD), start (HH:MM), end (HH:MM)
- Make descriptions professional and detailed WITHOUT quotes or extra punctuation
- Task descriptions should be plain text without surrounding quotes
- Set billable to true for development work, false for meetings
- Spread tasks across working days realistically
- DO NOT wrap task descriptions in quotes - use plain text only

Example format:
2024-06-15,09:00,11:00,Implement user authentication system,Backend Development,Authentication,true
2024-06-15,11:15,12:00,Code review for login functionality,Code Review,Review,true

Return ONLY the CSV data without any additional text or formatting.
"""
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