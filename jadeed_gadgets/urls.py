"""
URL configuration for jadeed_gadgets project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')), 
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('seller/', include('products.seller_urls')),
    path('', include('visualsearch.urls')),  # Visual search functionality - temporarily disabled
    path('', include('chatbot.urls')),  # Chatbot functionality - temporarily disabled
    path('recommendations/', include('recommendations.urls')),  # AI-powered recommendations
    path('price-comparison/', include('price_comparison.urls')),  # Price comparison with competitors
    
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
