# WorkFlow-AI-Journal 🤖📊

An intelligent automation tool that generates professional work journals from GitHub commits using AI, automatically tracks time in Clockify, and creates comprehensive reports for performance reviews and appraisals.

## ✨ Features

- **🔗 Multi-API Integration**: Seamlessly connects GitHub, Clockify, and Google Gemini AI
- **🧠 Future-Proof AI Model Selection**: Dynamically adapts to new Gemini releases (2.5, 3.0, 4.0+) with intelligent scoring
- **🎯 Thinking Model Priority**: Automatically selects thinking models for superior reasoning and analysis
- **📅 Natural Language Date Processing**: Parse "last 2 weeks", "this month", "yesterday" and more
- **⚡ Smart Workflow Orchestration**: Complete end-to-end automation with intelligent gap detection
- **🤖 AI-Powered Task Generation**: Converts GitHub commits into detailed, time-estimated tasks
- **⏰ Automatic Time Tracking**: Creates time entries in Clockify with realistic duration estimates
- **📊 Intelligent Reporting**: Generates Excel reports for any time range (weeks, months, quarters)
- **🏢 Organization Repository Access**: Works with both personal and organization repositories
- **🔒 Security-First**: Secure API key management without hardcoded credentials
- **🛡️ Smart Error Handling**: Comprehensive error handling with helpful user guidance
- **📱 Interactive CLI**: Powerful command-line interface with guided workflows

## 🎯 **Enhanced Phase 2 Features**

### 📅 **Smart Task Scheduling**
- **Distribution Options**: Choose between spreading tasks evenly or keeping exact commit times
- **Business Hours Enforcement**: Automatically adjusts times to 9 AM - 6 PM working hours  
- **Intelligent Spacing**: Adds breaks between tasks and avoids scheduling conflicts

### 🏢 **Weekly Meeting Integration**
- **Automatic Scheduling**: Add recurring weekly meetings to your time tracking
- **Flexible Configuration**: Set meetings for any day/time with custom duration
- **Multiple Meetings**: Support for standups, reviews, planning sessions, etc.
- **Professional Organization**: Custom meeting titles and proper categorization

### 🤖 **Enhanced AI Task Generation**
- **Quote-Free Descriptions**: Clean, professional task descriptions without formatting issues
- **Business-Appropriate**: Professional task naming suitable for corporate environments
- **Thinking Model Power**: Leverages latest AI reasoning for accurate time estimates
- **Context-Aware**: Considers realistic development patterns and work complexity

## 🧠 **Dynamic AI Model Selection**

WorkFlow-AI-Journal features an intelligent model selection system that automatically adapts to new Google Gemini releases:

### 🏆 **Scoring Algorithm**
```
🧠 Thinking Models: +10,000 points (highest priority)
🔢 Version Scoring: Major × 1,000 + Minor × 100
🚀 Future Versions (4.0+): +500 bonus  
🌟 Next-Gen (3.0+): +200 bonus
⚡ Model Types: Ultra (+500), Pro (+400), Flash (+300)
🧪 Experimental: +200 bonus
```

### 🎯 **Automatic Priority**
1. **Gemini 3.0-Flash-Thinking** → Score: ~13,500 (Future release ready)
2. **Gemini 2.5-Pro-Thinking** → Score: ~12,900 (Hypothetical)  
3. **Gemini 2.0-Flash-Thinking** → Score: ~12,500 (Current best)

**No code updates needed** - the system automatically detects and uses the latest optimal model!

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/WorkFlow-AI-Journal.git
cd WorkFlow-AI-Journal
pip install -r requirements.txt
```

### 2. Configure API Keys
Create or edit the `_API_KEYS` file:
```
CLOCKIFY_API_KEY=your_clockify_api_key
CLOCKIFY_WORKSPACE_ID=your_workspace_id
CLOCKIFY_PROJECT_ID=your_project_id
GEMINI_API_KEY=your_gemini_api_key
GITHUB_API_KEY=your_github_token
```

### 3. Test Connections
```bash
python test_apis.py
```

### 4. Import Existing Tasks (Optional)
```bash
python clockify_import_csv_api.py
```

## 🔧 How to Get API Keys

### Clockify API
1. Go to [Clockify Settings](https://clockify.me/user/settings)
2. Navigate to API section
3. Generate API key
4. Get Workspace ID from your workspace URL
5. Create a project and note its ID

### Google Gemini AI
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API key"
3. Select or create a Google Cloud project
4. Copy the generated key

### GitHub Personal Access Token
1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (private repos) or `public_repo` (public only)
4. Generate and copy the token

## 📋 Usage Workflow

1. **🗣️ Natural Language Query**: "Generate report for last 2 weeks"
2. **📅 Smart Date Processing**: Automatically calculates date ranges and business days
3. **🔍 Gap Analysis**: Identifies missing Clockify entries for work days
4. **📦 Commit Retrieval**: Fetches relevant GitHub commits for missing periods
5. **🧠 AI Task Generation**: Gemini AI creates realistic task descriptions with time estimates
6. **⚡ Auto-Import**: Tasks are automatically added to Clockify
7. **📊 Report Export**: Generates comprehensive reports for the requested period

### 🎯 **Complete Automation Example**

```bash
python agent.py
# Choose option 3: Generate work report
# Enter: "last 2 weeks"
# Select repository or use default
# Review and confirm task import
# ✅ Done! All missing work entries created automatically
```

## 🛡️ Security & Privacy

- **No Hardcoded Secrets**: All API keys stored in local `_API_KEYS` file
- **Environment Variables**: Secure configuration loading
- **Local Processing**: Your data stays on your machine
- **Open Source**: Full transparency - inspect the code yourself
- **No Data Collection**: We don't collect or store your personal data

## 🧪 Testing

Run the test suite to verify all connections:
```bash
python test_apis.py
```

Test the dynamic model selection algorithm:
```bash
python test_dynamic_selection.py
```

Test Phase 2 core logic:
```bash
python test_phase2.py
```

Diagnose Gemini API issues:
```bash
python fix_gemini.py
```

This will:
- ✅ Test API key configuration
- ✅ Verify Clockify connection
- ✅ Check GitHub access
- ✅ Validate Gemini AI setup with best model
- ✅ Test natural language date parsing
- ✅ Validate workflow orchestration
- ✅ Demonstrate dynamic version scoring

## 📁 Project Structure

```
WorkFlow-AI-Journal/
├── config.py              # Secure configuration management
├── clockify_api.py         # Clockify integration
├── github_api.py           # GitHub API wrapper
├── gemini_api.py          # Google Gemini AI integration
├── test_apis.py           # API connection tests
├── clockify_import_csv_api.py  # CSV import utility
├── clockify_tasks.csv     # Sample task data
├── _API_KEYS             # Your API credentials (local only)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🤝 Contributing

We welcome contributions! This project is designed to be:
- **Learning-Friendly**: Great for understanding AI agent development
- **Collaborative**: Pull requests welcome
- **Educational**: Well-documented code for learning

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - You're free to use, modify, and distribute this project. See [LICENSE](LICENSE) for details.

## 📚 Citation

If you use this project in your research or work, you can cite it as:

```bibtex
@software{workflow_ai_journal,
  title={WorkFlow-AI-Journal: Automated Work Tracking with AI},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/WorkFlow-AI-Journal}
}
```

## 🚧 Roadmap

- [x] **Phase 1**: Core API integrations ✅
- [x] **Phase 2**: Core logic and workflow automation ✅  
- [ ] **Phase 3**: Excel report generation and advanced analytics
- [ ] **Phase 4**: Web UI interface
- [ ] **Phase 5**: Advanced AI features and learning
- [ ] **Phase 6**: Team collaboration features

**Current Status**: Phase 2 Complete - Full workflow automation ready! 🎉

## ❓ Troubleshooting

### Common Issues

**"Import could not be resolved" errors**
```bash
pip install -r requirements.txt
```

**API connection failures**
- Verify API keys in `_API_KEYS` file
- Check internet connection
- Run `python test_apis.py` for detailed diagnosis

**Clockify time entries not appearing**
- Ensure correct workspace and project IDs
- Check time zone settings
- Verify project permissions

## 🆘 Support

- 📖 **Documentation**: Check this README and code comments
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Discussion section on GitHub
- 🤝 **Community**: Join our discussions

---

**Made with ❤️ for developers who want to automate their work tracking and create better performance reviews.**