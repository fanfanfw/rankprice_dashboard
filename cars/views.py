from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
from django.shortcuts import render
from .models import Car
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from .models import CarBrand
from django.db.models import IntegerField
from django.db.models.functions import Cast
from .tasks import sync_mudahmy_to_main, sync_carlistmy_to_main

@csrf_exempt
def get_price_rank(request):
    """API untuk menentukan ranking harga mobil berdasarkan harga, millage, tahun, dan variant."""
    
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    try:
        data = json.loads(request.body)
        brand = data.get("brand")
        model = data.get("model")
        variant = data.get("variant")
        price = data.get("price")
        millage = data.get("millage")
        year = data.get("year")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    if not variant:
        variant = model
        
    # Validasi input
    if not (brand and model and variant and price and millage and year):
        return JsonResponse({"error": "Brand, model, price, millage, dan year harus diisi!"}, status=400)

    try:
        price_numeric = int(price)
        millage_numeric = int(millage)
        year_numeric = int(year)
    except ValueError:
        return JsonResponse({"error": "Format harga, millage, atau tahun tidak valid!"}, status=400)

    # Query untuk menghitung ranking
    query = """
    WITH stats AS (
    SELECT 
        AVG(price) AS avg_price, 
        STDDEV(price) AS stddev_price,
        AVG(millage) AS avg_millage, 
        STDDEV(millage) AS stddev_millage,
        AVG(year) AS avg_year, 
        STDDEV(year) AS stddev_year
    FROM cars
    WHERE brand = %s 
      AND (model = %s OR variant = %s)
      AND price IS NOT NULL AND millage IS NOT NULL AND year IS NOT NULL
),
ranked_cars AS (
    SELECT 
        id,
        brand,
        model,
        variant,
        price,
        millage,
        year,
        source,
        - ( (price - stats.avg_price) / NULLIF(stats.stddev_price, 0) )
        - 2 * ( (millage - stats.avg_millage) / NULLIF(stats.stddev_millage, 0) )
        + 1.5 * ( (year - stats.avg_year) / NULLIF(stats.stddev_year, 0) ) AS score,
        RANK() OVER (ORDER BY 
            - ( (price - stats.avg_price) / NULLIF(stats.stddev_price, 0) )
            - 2 * ( (millage - stats.avg_millage) / NULLIF(stats.stddev_millage, 0) )
            + 1.5 * ( (year - stats.avg_year) / NULLIF(stats.stddev_year, 0) ) DESC
        ) AS rank
    FROM cars, stats
    WHERE brand = %s 
      AND (model = %s OR variant = %s)
      AND price IS NOT NULL AND millage IS NOT NULL AND year IS NOT NULL
    ),
    user_rank AS (
        SELECT COUNT(*) + 1 AS user_rank
        FROM ranked_cars
        WHERE score > (
            ( (%s - (SELECT avg_price FROM stats)) / NULLIF((SELECT stddev_price FROM stats), 0) ) -
            2 * ( (%s - (SELECT avg_millage FROM stats)) / NULLIF((SELECT stddev_millage FROM stats), 0) ) +
            1.5 * ( (%s - (SELECT avg_year FROM stats)) / NULLIF((SELECT stddev_year FROM stats), 0) )
        )
    ),
    total_count AS (
        SELECT COUNT(*) AS total FROM ranked_cars
    ),
    source_counts AS (
        SELECT source, COUNT(*) AS count FROM ranked_cars GROUP BY source
    ),
    top_cars AS (
        SELECT id, brand, model, variant, price, millage, year, source, rank
        FROM ranked_cars
        ORDER BY rank ASC
        LIMIT 5
    ),
    bottom_cars AS (
        SELECT id, brand, model, price, variant, millage, year, source, rank
        FROM ranked_cars
        ORDER BY rank DESC
        LIMIT 5
    )
    SELECT 
        (SELECT user_rank FROM user_rank) AS user_rank,
        (SELECT total FROM total_count) AS total,
        (SELECT jsonb_agg(jsonb_build_object(
            'id', id,
            'brand', brand,
            'model', model,
            'variant', variant,
            'year', year,
            'price', price,
            'millage', millage,
            'source', source,
            'rank', rank
        )) FROM top_cars) AS top_5,
        (SELECT jsonb_agg(jsonb_build_object(
            'id', id,
            'brand', brand,
            'model', model,
            'variant', variant,
            'year', year,
            'price', price,
            'millage', millage,
            'source', source,
            'rank', rank
        )) FROM bottom_cars) AS bottom_5,
        (SELECT jsonb_object_agg(source, count) FROM source_counts) AS source_distribution;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [brand, model, variant, brand, model, variant, 
                               price_numeric, millage_numeric, year_numeric])
        result = cursor.fetchone()

    if not result or result[0] is None:
        return JsonResponse({"message": "Mobil tidak ditemukan di database"}, status=404)

    # Parsing JSON strings to Python objects
    top_5 = json.loads(result[2]) if isinstance(result[2], str) else result[2]
    bottom_5 = json.loads(result[3]) if isinstance(result[3], str) else result[3]
    source_distribution = json.loads(result[4]) if isinstance(result[4], str) else result[4]

    response_data = {
        "brand": brand,
        "model": model,
        "variant": variant,
        "price": price_numeric,
        "millage": millage_numeric,
        "year": year_numeric,
        "ranking": result[0],
        "total_listings": result[1],
        "source_distribution": source_distribution,
        "top_5": top_5,
        "bottom_5": bottom_5,
        "message": f"Dengan harga yang Anda ajukan, Anda berada di peringkat {result[0]} dari {result[1]} listing."
    }

    return JsonResponse(response_data, json_dumps_params={'indent': 4})


def index(request):
    return render(request, "rank_check.html")

def dashboard(request):
    """Tampilkan dashboard"""
    return render(request, 'dashboard.html')

def cars_list(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search_value = request.GET.get("search[value]", "").strip()
    brand_filter = request.GET.get("brand", "").strip()
    model_filter = request.GET.get("model", "").strip()
    variant_filter = request.GET.get("variant", "").strip()
    source_filter = request.GET.get("source", "").strip()

    # Perbarui daftar kolom sesuai urutan yang tampil di DataTables
    valid_columns = [
        "id", "brand", "model", "variant", "price", 
        "millage", "year", "transmission", "source", "image", "listing_url"
    ]
    order_column_index = int(request.GET.get("order[0][column]", 0))
    order_direction = request.GET.get("order[0][dir]", "asc")

    if order_column_index < len(valid_columns):
        order_column = valid_columns[order_column_index]
    else:
        order_column = "id"  # fallback default

    if order_direction == "desc":
        order_column = f"-{order_column}"

    # Query utama dengan cast untuk kolom numerik
    query = Car.objects.annotate(
        price_int=Cast("price", IntegerField()),
        millage_int=Cast("millage", IntegerField()),
        year_int=Cast("year", IntegerField()),
    )

    # Filter berdasarkan dropdown
    if brand_filter:
        query = query.filter(brand=brand_filter)

    if model_filter:
        query = query.filter(Q(model=model_filter) | Q(variant=model_filter))

    if source_filter:
        query = query.filter(source=source_filter)

    # Filter pencarian umum, termasuk pencarian berdasarkan id jika input berupa angka
    if search_value:
        id_query = Q()
        if search_value.isdigit():
            # Jika input angka, tambahkan filter untuk id
            id_query = Q(id=int(search_value))
        query = query.filter(
            id_query |
            Q(brand__icontains=search_value) |
            Q(model__icontains=search_value) |
            Q(variant__icontains=search_value) |
            Q(price__icontains=search_value) |
            Q(millage__icontains=search_value) |
            Q(year__icontains=search_value) |
            Q(transmission__icontains=search_value) |
            Q(source__icontains=search_value)
        )

    total_records = query.count()

    # Lakukan penggantian untuk kolom numerik
    order_column = order_column.replace("price", "price_int")\
                               .replace("millage", "millage_int")\
                               .replace("year", "year_int")

    query = query.order_by(order_column)
    query = query[start:start+length]

    data = [
        {
            "id": car.id,
            "brand": car.brand,
            "model": car.model,
            "variant": car.variant,
            "price": car.price_int,
            "millage": car.millage_int,
            "year": car.year_int,
            "transmission": car.transmission,
            "source": car.source,
            "image": car.gambar[0] if car.gambar else "",
            "listing_url": car.listing_url
        }
        for car in query
    ]

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })




def get_first_image(image_list):
    """Mengambil gambar pertama dari array gambar yang ada di database."""
    if not image_list:
        return None  # Jika tidak ada gambar, kembalikan None
    if isinstance(image_list, list):  # Jika sudah berbentuk list, ambil elemen pertama
        return image_list[0]
    if isinstance(image_list, str) and image_list.startswith("{"):  
        # Jika gambar berbentuk string dengan format array PostgreSQL (tanpa parsing JSON)
        images = image_list.strip("{}").split(",")  # Parsing format PostgreSQL array
        return images[0] if images else None
    return None

def get_filter_options(request):
    """API untuk mengambil daftar filter unik"""
    brands = Car.objects.values_list("brand", flat=True).distinct()
    models = Car.objects.values_list("model", flat=True).distinct()
    sources = Car.objects.values_list("source", flat=True).distinct()

    return JsonResponse({
        "brands": list(brands),
        "models": list(models),
        "sources": list(sources),
    })

def get_brands(request):
    """API untuk mengambil daftar brand unik dari tabel cars_brand (ascending)"""
    brands = (
        CarBrand.objects
        .order_by('brand')                 # Tambahkan ini
        .values_list('brand', flat=True)
        .distinct()
    )
    return JsonResponse({"brands": list(brands)})


def get_models(request):
    """API untuk mengambil daftar model berdasarkan brand dari tabel cars_brand"""
    brand = request.GET.get("brand", "")
    if not brand:
        return JsonResponse({"models": []})  # Jika tidak ada brand yang dipilih, kembalikan array kosong

    models = (
        CarBrand.objects
        .filter(brand=brand)
        .order_by('model')                 # Tambahkan ini
        .values_list('model', flat=True)
        .distinct()
    )
    return JsonResponse({"models": list(models)})


def start_sync_mudahmy(request):
    # Memanggil tugas Celery secara asynchronous
    task_result = sync_mudahmy_to_main.delay()
    return JsonResponse({
        "message": "Sync MudahMy started. Silakan cek logs atau Celery monitoring.",
        "task_id": task_result.id
    })

def start_sync_carlist(request):
    task_result = sync_carlistmy_to_main.delay()
    return JsonResponse({
        "message": "Sync Carlist started. Silakan cek logs atau Celery monitoring.",
        "task_id": task_result.id
    })