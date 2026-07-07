from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import login_page, dashboard_page

urlpatterns = [
    # HTML СТРАНИЦЫ
    path('', login_page, name='home'),                     # При заходе на 127.0.0.1:8000 сразу откроется логин
    path('login/', login_page, name='login'),              # 127.0.0.1:8000/login/
    path('dashboard/', dashboard_page, name='dashboard'),  # 127.0.0.1:8000/dashboard/

    # АДМИНКА
    path('admin/', admin.site.urls),

    # API И АВТОРИЗАЦИЯ
    path('api/v1/sales/', include('core.urls')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # SWAGGER ДОКУМЕНТАЦИЯ
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]