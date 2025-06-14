from django.urls import path, include
from orchestrator import urls as orchestrator_urls

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', include(orchestrator_urls)),
]
