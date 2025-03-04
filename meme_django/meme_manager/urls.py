from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('memes/', views.meme_list, name='meme_list'),
    path('memes/add/', views.add_meme, name='add_meme'),
    path('memes/edit/<int:meme_id>/', views.edit_meme, name='edit_meme'),
    path('memes/delete/<int:meme_id>/', views.delete_meme, name='delete_meme'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('models/', views.model_configuration, name='model_configuration'),
    path('models/activate/<int:config_id>/', views.activate_config, name='activate_config'),
    path('embeddings/regenerate/', views.regenerate_all_embeddings, name='regenerate_all_embeddings'),
    path('interactions/', views.interaction_history, name='interaction_history'),
    path('api/memes/', views.api_get_memes, name='api_get_memes'),
    path('api/interactions/', views.api_record_interaction, name='api_record_interaction'),
]