from .general_views import (
    home,
    about,
    contact,
    eligibility_guide,
    privacy_policy,
    terms_of_service,
)
from .auth_views import (
    register_view,
    login_view,
    logout_view,
    profile_view,
)
from .request_views import (
    request_create,
    request_detail,
    request_track,
    request_list,
    request_update_status,
    request_respond,
)
from .donor_views import (
    donor_register,
    donor_search,
    donor_detail,
    toggle_availability_api,
)
from .bloodbank_views import (
    bloodbank_list,
    bloodbank_detail,
    bloodbank_geojson_api,
)
from .dashboard_views import (
    dashboard_dispatcher,
    donor_dashboard,
    requester_dashboard,
    staff_dashboard,
    mark_notification_read,
    add_donation_record,
    verify_donor_staff_action,
)
