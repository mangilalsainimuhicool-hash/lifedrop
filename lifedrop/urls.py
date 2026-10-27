from django.urls import path
from lifedrop import views

urlpatterns = [
    # Static and General Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('eligibility/', views.eligibility_guide, name='eligibility_guide'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Dashboards
    path('dashboard/', views.dashboard_dispatcher, name='dashboard'),
    path('dashboard/donor/', views.donor_dashboard, name='donor_dashboard'),
    path('dashboard/requester/', views.requester_dashboard, name='requester_dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

    # Emergency Blood Requests
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/track/', views.request_track, name='request_track'),
    path('requests/<str:reference_id>/', views.request_detail, name='request_detail'),
    path('requests/<str:reference_id>/update-status/', views.request_update_status, name='request_update_status'),
    path('requests/<str:reference_id>/respond/', views.request_respond, name='request_respond'),

    # Donor Operations
    path('donors/', views.donor_search, name='donor_search'),
    path('donors/register/', views.donor_register, name='donor_register'),
    path('donors/<int:pk>/', views.donor_detail, name='donor_detail'),
    path('donors/log-donation/', views.add_donation_record, name='add_donation_record'),
    path('donors/<int:donor_id>/verify/', views.verify_donor_staff_action, name='verify_donor_staff_action'),
    path('api/donor/toggle-availability/', views.toggle_availability_api, name='toggle_availability_api'),

    # Blood Banks Directory
    path('blood-banks/', views.bloodbank_list, name='bloodbank_list'),
    path('blood-banks/<int:pk>/', views.bloodbank_detail, name='bloodbank_detail'),
    path('api/blood-banks/geojson/', views.bloodbank_geojson_api, name='bloodbank_geojson_api'),
]
