# JadeedBot - AI Chatbot for Jadeed Gadgets

JadeedBot is an AI-powered customer support chatbot integrated into the Jadeed Gadgets e-commerce website. It uses the Groq API with the Llama3-8B-8192 model to provide intelligent customer support.

## Features

- **24/7 Customer Support**: Instant responses to customer queries
- **Pakistani Context**: Uses localized phrases like "Assalamualaikum" and "Shukriya"
- **E-commerce Focus**: Helps with product searches, cart management, order tracking
- **Modern UI**: Clean, responsive chat interface with typing indicators
- **Smart Responses**: Contextual responses focused on actual website features
- **Mobile Friendly**: Responsive design that works on all devices

## Installation & Setup

### 1. Prerequisites

Ensure you have the following installed:
- Python 3.8+
- Django 5.2+
- httpx library

### 2. Install Required Dependencies

```bash
pip install httpx
```

### 3. Get Your Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Create a free account
3. Generate an API key
4. Keep your API key secure

### 4. Configure API Key

#### Option A: Environment Variable (Recommended)

**Windows:**
```cmd
setx GROQ_API_KEY "your-actual-api-key-here"
```

**Linux/Mac:**
```bash
export GROQ_API_KEY="your-actual-api-key-here"
# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export GROQ_API_KEY="your-actual-api-key-here"' >> ~/.bashrc
```

#### Option B: Direct Configuration (Development Only)

Edit `chatbot/views.py` and replace:
```python
GROQ_API_KEY = "your-groq-api-key-here"
```

#### Option C: Use Setup Script

Run the automated setup script:
```bash
python setup_groq_api.py
```

### 5. Django Setup

The chatbot is already configured in your Django project:

1. **App Added**: `chatbot` app is added to `INSTALLED_APPS`
2. **URLs Configured**: Chatbot URLs are included in main URLconf
3. **Templates Ready**: Chatbox template is included in base.html

### 6. Run the Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` and you'll see the chatbot button in the bottom right corner.

## Usage

### For Customers

1. **Access**: Click the chat button (💬) in the bottom right corner
2. **Chat**: Type your message and press Enter or click Send
3. **Quick Actions**: Use suggestion buttons for common queries
4. **Topics**: Ask about products, orders, payments, account help

### Example Conversations

**Product Search:**
- User: "Show me latest smartphones"
- Bot: "Assalamualaikum! You can browse our latest smartphones by using the search bar or visiting our products page. We have great deals on Samsung, iPhone, and other brands with PKR pricing!"

**Order Tracking:**
- User: "How to track my order?"
- Bot: "Assalamualaikum! To track your order, please login to your account and visit the Orders section. You'll find all your order details and tracking information there. Shukriya!"

## Customization

### Modifying Bot Behavior

Edit the `SYSTEM_PROMPT` in `chatbot/views.py` to customize:
- Response style and tone
- Available features to mention
- Specific product categories
- Pakistani cultural context

### UI Customization

Modify the styles in `templates/chatbot/chatbox.html`:
- Colors and gradients
- Chat bubble appearance
- Animation effects
- Mobile responsiveness

### Adding New Features

1. **Quick Replies**: Add more suggestion buttons
2. **Rich Messages**: Support for images, links, buttons
3. **Context Awareness**: Track conversation history
4. **Integration**: Connect with order/product databases

## API Configuration

### Groq API Settings

Current configuration in `chatbot/views.py`:
```python
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"
```

### Request Parameters

- **Temperature**: 0.7 (balanced creativity)
- **Max Tokens**: 200 (concise responses)
- **Stream**: False (full response)

## Security

- **CSRF Protection**: Properly configured for POST requests
- **Input Validation**: Message length limits and sanitization
- **Error Handling**: Graceful fallbacks for API failures
- **Rate Limiting**: Consider implementing for production

## File Structure

```
jadeed_gadgets/
├── chatbot/
│   ├── __init__.py
│   ├── views.py           # Main chatbot logic
│   ├── urls.py            # URL configuration
│   └── apps.py
├── templates/
│   └── chatbot/
│       ├── chatbox.html   # Chat interface
│       └── chatbot_page.html  # Test page
├── setup_groq_api.py      # API key setup script
└── JADEEDBOT_README.md    # This file
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Check if environment variable is set correctly
   - Restart terminal/IDE after setting environment variable
   - Verify API key is valid on Groq Console

2. **Chatbot Not Responding**
   - Check Django logs for errors
   - Verify internet connection
   - Check Groq API status

3. **Chat Window Not Appearing**
   - Clear browser cache
   - Check browser console for JavaScript errors
   - Verify templates are loading correctly

4. **CSRF Token Errors**
   - Ensure CSRF middleware is enabled
   - Check if CSRF token is properly included in requests

### Debug Mode

Enable debug logging in `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'chatbot': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

### Environment Variables

Set these in your production environment:
- `GROQ_API_KEY`: Your Groq API key
- `DEBUG`: False
- `ALLOWED_HOSTS`: Your domain

### Performance Optimization

- **Caching**: Implement Redis for session management
- **Rate Limiting**: Use Django-ratelimit
- **CDN**: Serve static files from CDN
- **Database**: Use PostgreSQL for production

### Security Checklist

- [ ] API key stored securely
- [ ] HTTPS enabled
- [ ] CSRF protection active
- [ ] Input validation in place
- [ ] Error handling implemented
- [ ] Rate limiting configured

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs
3. Test with a simple message first
4. Verify API key configuration

## License

This chatbot integration is part of the Jadeed Gadgets project.

---

**JadeedBot** - Making customer support smarter, one conversation at a time! 🤖✨
