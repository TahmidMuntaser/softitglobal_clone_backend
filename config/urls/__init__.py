from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def home(request):
    return redirect('/api/docs/')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/openapi/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('apps.catalog.urls')),
    path('api/', include('apps.orders.urls')),
]