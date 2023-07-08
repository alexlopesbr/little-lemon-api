from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register('category', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('cart/menu-items', views.CartView.as_view()),

    path('groups/manager/users', views.ManagerUsersView.as_view()),
    path('groups/manager/users/<int:pk>', views.ManagerSingleUserView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewManagement.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewManagementSingleView.as_view()),

    path('menu-items', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleItemView.as_view()),

    path('orders/', views.OrdersView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),

    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist', TokenBlacklistView.as_view(), name='token_blacklist'),
]

urlpatterns += router.urls
