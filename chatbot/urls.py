from django.urls import path
from . import views

urlpatterns = [
    path('chatbot-response/', views.chatbot_response, name='chatbot_response'),
    path('chatbot/', views.chatbot_page, name='chatbot_page'),  # Optional: for testing
]
