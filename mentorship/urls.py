from django.urls import path
from . import views

urlpatterns = [
    # Old mentorship system (keep for backward compatibility)
    path('old/', views.MentorshipOfferListView.as_view(), name='mentorship_list_old'),
    path('old/<int:pk>/', views.MentorshipOfferDetailView.as_view(), name='mentorship_detail_old'),
    path('old/create/', views.MentorshipOfferCreateView.as_view(), name='mentorship_create_old'),
    path('old/<int:offer_id>/apply/', views.MentorshipApplicationCreateView.as_view(), name='mentorship_apply_old'),
    path('old/manage/', views.manage_mentorship, name='mentorship_manage_old'),
    
    # New mentor management system
    path('', views.available_mentors, name='mentorship_list'),
    path('available/', views.available_mentors, name='available_mentors'),
    path('mentor/<int:pk>/enroll/', views.mentor_enroll_check, name='mentor_enroll_check'),
    path('mentor/<int:pk>/confirm/', views.mentor_enroll_confirm, name='mentor_enroll_confirm'),
    path('my-mentorships/', views.my_mentorships, name='my_mentorships'),
    path('chat/<uuid:tracking_id>/', views.mentorship_chat, name='mentorship_chat'),
    path('mentor-dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
]