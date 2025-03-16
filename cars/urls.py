from django.urls import path
from .views import get_price_rank, cek_ranking, dashboard, cars_list, get_filter_options, get_brands, get_models, start_sync_mudahmy, start_sync_carlist, login_view, logout_view, test

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('price_rank/', get_price_rank, name='price-rank'),

    # path('dashboard/', dashboard, name='dashboard'),
    path('api/cars/', cars_list, name='cars-list'),
    path('api/filters/', get_filter_options, name='get-filter-options'),
    path('api/brands/', get_brands, name='get-brands'),
    path('api/models/', get_models, name='get-models'),
    path('sync_mudahmy/', start_sync_mudahmy, name='sync_mudahmy'),
    path('sync_carlist/', start_sync_carlist, name='sync_carlist'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('cek-ranking/', cek_ranking, name='cek_ranking'),

    path('test/', test, name="test")

]
