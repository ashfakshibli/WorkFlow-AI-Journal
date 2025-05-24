# WorkFlow-AI-Journal 🤖📊

An intelligent automation tool that generates professional work journals from GitHub commits using AI, automatically tracks time in Clockify, and creates comprehensive reports for performance reviews and appraisals.

## ✨ Features

- **🔗 Multi-API Integration**: Seamlessly connects GitHub, Clockify, and Google Gemini AI
- **🧠 Intelligent AI Model Selection**: Automatically selects the best Gemini model (prioritizes thinking models for superior reasoning)
- **🤖 AI-Powered Task Generation**: Converts GitHub commits into detailed, time-estimated tasks
- **⏰ Automatic Time Tracking**: Creates time entries in Clockify with realistic duration estimates
- **📊 Intelligent Reporting**: Generates Excel reports for any time range (weeks, months, quarters)
- **🏢 Organization Repository Access**: Works with both personal and organization repositories
- **🔒 Security-First**: Secure API key management without hardcoded credentials
- **🛡️ Smart Error Handling**: Comprehensive error handling with helpful user guidance
- **📱 Simple Interface**: Clean command-line interface (CLI coming soon)

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

1. **Query Time Range**: Ask the agent for reports (e.g., "last 2 weeks")
2. **Data Check**: System checks existing Clockify entries
3. **Gap Analysis**: Identifies missing time entries
4. **Commit Retrieval**: Fetches GitHub commits for missing periods
5. **AI Generation**: Gemini AI creates realistic task descriptions with time estimates
6. **Auto-Import**: Tasks are automatically added to Clockify
7. **Report Export**: Generates Excel report for the requested period

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

This will:
- ✅ Test API key configuration
- ✅ Verify Clockify connection
- ✅ Check GitHub access
- ✅ Validate Gemini AI setup

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

- [ ] **Phase 1**: Core API integrations ✅
- [ ] **Phase 2**: AI task generation
- [ ] **Phase 3**: Excel report generation
- [ ] **Phase 4**: Web UI interface
- [ ] **Phase 5**: Advanced analytics
- [ ] **Phase 6**: Team collaboration features

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