import json
import httpx
import os
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.db.models import Q
from products.models import Product
import logging

logger = logging.getLogger(__name__)

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# Get Groq API key from environment variable
# Set environment variable: GROQ_API_KEY="your-actual-api-key"
# For development, you can set it here temporarily (not recommended for production)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', "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")

# JadeedBot system prompt
SYSTEM_PROMPT = """You are JadeedBot, a helpful support assistant for Jadeed Gadgets - a Pakistani electronics e-commerce website. 

IMPORTANT GUIDELINES:
- You help guests and buyers ONLY (ignore any seller/admin concerns)
- Always greet with "Assalamualaikum" and use "Shukriya" for thanks
- Use short, helpful, friendly sentences
- Display all prices in PKR format (e.g., Rs. 149,999)
- Never mention you are an AI or language model
- Only refer to actual website features:
  * Product browsing and filtering
  * Shopping cart functionality
  * Order tracking
  * User account management
  * Wishlist features
  * Visual search (camera icon)
  * PKR pricing
  * Login/registration
  * Electronics categories (smartphones, laptops, headphones, etc.)
  
WHEN TO GUIDE TO LOGIN:
- Cart access requires login
- Order tracking requires login
- Wishlist requires login
- Account settings require login

RESPONSE STYLE:
- Keep responses under 50 words when possible
- Be conversational and friendly
- Use Pakistani context and expressions
- Focus on helping customers find products and navigate the site
- If asked about something not related to the website, politely redirect to website features

Remember: You are a customer support bot for Jadeed Gadgets e-commerce site, not a general AI assistant.

IMPORTANT: If a user asks about specific products, prices, or availability, I will provide you with actual product data from our database. Use this real data in your responses instead of giving general guidance."""

def search_products(query, category=None, max_price=None, min_price=None, limit=5):
    """Search for products based on query and filters"""
    try:
        # Start with active products
        products = Product.objects.filter(is_active=True)
        
        # Filter by category if specified
        if category:
            products = products.filter(category__icontains=category)
        
        # Filter by price range
        if max_price:
            products = products.filter(price__lte=max_price)
        if min_price:
            products = products.filter(price__gte=min_price)
        
        # Search in name, brand, description, and tags
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Order by relevance (featured first, then by price)
        products = products.order_by('-is_featured', 'price')[:limit]
        
        # Format product data for the chatbot
        product_list = []
        for product in products:
            product_data = {
                'name': product.name,
                'brand': product.brand,
                'price': float(product.price),
                'category': product.get_category_display(),
                'ram': product.ram,
                'processor': product.processor,
                'storage': product.storage,
                'screen_size': product.screen_size,
                'stock': product.stock,
                'rating': product.rating,
                'is_featured': product.is_featured,
                'is_flash_sale': product.is_flash_sale
            }
            product_list.append(product_data)
        
        return product_list
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []

def extract_search_info(message):
    """Extract search information from user message"""
    message_lower = message.lower()
    
    # Extract price information
    price_match = re.search(r'under\s+(?:rs\.?\s*)?([0-9,]+)', message_lower)
    max_price = None
    if price_match:
        max_price = float(price_match.group(1).replace(',', ''))
    
    # Extract category information
    category = None
    if 'laptop' in message_lower or 'laptops' in message_lower:
        category = 'laptop'
    elif 'mobile' in message_lower or 'phone' in message_lower or 'smartphone' in message_lower:
        category = 'mobile'
    elif 'tablet' in message_lower or 'tablets' in message_lower:
        category = 'tablet'
    elif 'accessory' in message_lower or 'accessories' in message_lower:
        category = 'accessory'
    
    # Extract brand information
    brands = ['apple', 'samsung', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'msi', 'lg', 'sony', 'xiaomi', 'oppo', 'vivo', 'huawei', 'realme', 'infinix', 'tecno']
    brand_query = None
    for brand in brands:
        if brand in message_lower:
            brand_query = brand
            break
    
    # Extract general search terms
    search_terms = []
    if brand_query:
        search_terms.append(brand_query)
    
    # Look for specific product features
    if 'gaming' in message_lower:
        search_terms.append('gaming')
    if 'business' in message_lower:
        search_terms.append('business')
    if 'student' in message_lower:
        search_terms.append('student')
    
    return {
        'category': category,
        'max_price': max_price,
        'brand': brand_query,
        'search_query': ' '.join(search_terms) if search_terms else None
    }

def format_product_data_for_ai(products, search_info):
    """Format product data for inclusion in AI prompt"""
    if not products:
        return "No products found matching the criteria."
    
    formatted_data = "Here are the available products from our database:\n\n"
    
    for i, product in enumerate(products, 1):
        formatted_data += f"{i}. {product['name']} by {product['brand']}\n"
        formatted_data += f"   Price: Rs. {product['price']:,.0f}\n"
        
        if product['ram']:
            formatted_data += f"   RAM: {product['ram']}\n"
        if product['processor']:
            formatted_data += f"   Processor: {product['processor']}\n"
        if product['storage']:
            formatted_data += f"   Storage: {product['storage']}\n"
        if product['screen_size']:
            formatted_data += f"   Screen: {product['screen_size']}\n"
        
        if product['stock'] > 0:
            formatted_data += f"   Stock: Available ({product['stock']} units)\n"
        else:
            formatted_data += f"   Stock: Out of Stock\n"
        
        if product['rating'] > 0:
            formatted_data += f"   Rating: {product['rating']}/5\n"
        
        if product['is_featured']:
            formatted_data += f"   ⭐ Featured Product\n"
        if product['is_flash_sale']:
            formatted_data += f"   🔥 Flash Sale!\n"
        
        formatted_data += "\n"
    
    return formatted_data

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_response(request):
    """Handle chatbot messages and return Groq API response"""
    try:
        # Parse the incoming message
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Check if the user is asking about products
        search_info = extract_search_info(user_message)
        product_data = ""
        
        # If the query seems to be about products, search the database
        if search_info['category'] or search_info['max_price'] or search_info['brand'] or search_info['search_query']:
            products = search_products(
                query=search_info['search_query'],
                category=search_info['category'],
                max_price=search_info['max_price']
            )
            
            if products:
                product_data = format_product_data_for_ai(products, search_info)
        
        # Prepare the message for Groq API
        system_message = SYSTEM_PROMPT
        if product_data:
            system_message += f"\n\nCURRENT PRODUCT DATA:\n{product_data}\n\nUse this real product data in your response. Show specific product names, prices, and details."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # Make request to Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 200,
            "stream": False
        }
        
        # Send request to Groq API using httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(GROQ_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                groq_response = response.json()
                bot_message = groq_response['choices'][0]['message']['content']
                
                return JsonResponse({
                    'response': bot_message,
                    'success': True
                })
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return JsonResponse({
                    'response': 'Assalamualaikum! I apologize, but I\'m having trouble connecting right now. Please try again in a moment. Shukriya for your patience!',
                    'success': False
                }, status=500)
                
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        return JsonResponse({
            'response': 'Assalamualaikum! I\'m having connection issues. Please try again in a moment. Shukriya!',
            'success': False
        }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({
            'response': 'Assalamualaikum! Something went wrong. Please try again. Shukriya for your understanding!',
            'success': False
        }, status=500)


def chatbot_page(request):
    """Render chatbot page for testing (optional)"""
    return render(request, 'chatbot/chatbot_page.html')
