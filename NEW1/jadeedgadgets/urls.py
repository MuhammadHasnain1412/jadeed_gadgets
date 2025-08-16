# from django.contrib import admin
# from django.urls import path, include
# from core import views

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.home, name='home'),
#     path('recommendations/', views.recommended_products, name='recommendations'),
    
#     # ✅ Add this line to enable built-in login/logout views
#     path('accounts/', include('django.contrib.auth.urls')),
# ]
from django.contrib import admin
from django.urls import path, include
from core.views import home, recommended_products  # Import your views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('recommendations/', recommended_products, name='recommendations'),
    path('accounts/', include('django.contrib.auth.urls')),  # ✅ Built-in login/logout/etc.
    path('', include('core.urls')),
    path('', include('NEW1.urls')),
]

# path('', include('core.urls')),  # Mount core app routes
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

