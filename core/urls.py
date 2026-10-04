from network import views as network_views
"""
URL configuration for core project.

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
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', network_views.register_view, name='register'),
    path('api/server-stats/', network_views.server_stats_api, name='server_stats_api'),
    path('admin/network/auditlog/metrics/<str:metric_type>/', network_views.server_metric_history, name='server_metric_history'),
    path('api/server-metrics/<str:metric_type>/', network_views.server_metric_history_api, name='server_metric_history_api'),
    path('admin/network/calculator/', network_views.ip_calculator_view, name='ip_calculator'),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
