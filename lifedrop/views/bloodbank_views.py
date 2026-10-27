import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Prefetch

from lifedrop.models import BloodBank, BloodInventory, BloodGroup
from lifedrop.forms import BloodBankFilterForm


def bloodbank_list(request):
    """
    Directory of certified blood banks with real-time stock indicators
    and OpenStreetMap Leaflet visualization.
    """
    form = BloodBankFilterForm(request.GET)
    city_filter = request.GET.get('city', '').strip()
    blood_group_filter = request.GET.get('blood_group', '').strip()

    queryset = BloodBank.objects.filter(is_verified=True).prefetch_related('inventories')

    if city_filter:
        queryset = queryset.filter(city__icontains=city_filter)

    if blood_group_filter:
        queryset = queryset.filter(
            inventories__blood_group=blood_group_filter,
            inventories__units_available__gt=0
        ).distinct()

    # Map markers data for Leaflet
    map_markers = []
    for bank in queryset:
        if bank.latitude and bank.longitude:
            inv_summary = ", ".join([
                f"{inv.blood_group}: {inv.units_available}u"
                for inv in bank.inventories.all()[:4]
            ])
            map_markers.append({
                'name': bank.name,
                'city': bank.city,
                'lat': float(bank.latitude),
                'lng': float(bank.longitude),
                'address': bank.address,
                'phone': bank.contact_phone,
                'hours': bank.operating_hours,
                'inventory': inv_summary or 'Stock verified on call',
                'url': f"/blood-banks/{bank.id}/",
            })

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'map_markers_json': json.dumps(map_markers),
        'selected_city': city_filter,
        'selected_blood_group': blood_group_filter,
    }
    return render(request, 'blood_banks/bloodbank_list.html', context)


def bloodbank_detail(request, pk):
    """
    Detailed profile for a specific blood bank including complete inventory breakdown.
    """
    bank = get_object_or_404(BloodBank.objects.prefetch_related('inventories'), pk=pk)
    inventories = bank.inventories.all().order_by('blood_group')

    context = {
        'bank': bank,
        'inventories': inventories,
    }
    return render(request, 'blood_banks/bloodbank_detail.html', context)


def bloodbank_geojson_api(request):
    """
    JSON API returning geo-tagged blood banks for map markers.
    """
    banks = BloodBank.objects.filter(is_verified=True, latitude__isnull=False, longitude__isnull=False)
    data = []
    for b in banks:
        data.append({
            'id': b.id,
            'name': b.name,
            'city': b.city,
            'lat': float(b.latitude),
            'lng': float(b.longitude),
            'phone': b.contact_phone,
            'hours': b.operating_hours,
            'address': b.address,
        })
    return JsonResponse({'blood_banks': data})
