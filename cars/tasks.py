# cars/tasks.py

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models_mudahmy import CarMudahMy
from .models_carlistmy import CarCarlistMy
from .models import Car

def parse_price(price_str: str) -> int or None:
    """
    Mengubah string price seperti 'RM 37,800' menjadi integer 37800.
    Jika gagal parse, return None.
    """
    if not price_str:
        return None
    # Hilangkan 'RM' (case-insensitive), spasi, dan koma
    tmp = price_str.upper().replace('RM', '').strip()
    tmp = tmp.replace(' ', '').replace(',', '')
    try:
        return int(tmp)
    except:
        return None

def parse_millage(millage_str: str) -> int or None:
    """
    Mengambil nilai tertinggi dari string millage seperti:
      - '100k - 109k' -> 109000
      - '40 - 45K km' -> 45000
    Jika gagal parse, return None.
    """
    if not millage_str:
        return None

    # Split dengan '-', ambil bagian terakhir (nilai tertinggi)
    last_part = millage_str.split('-')[-1].lower().strip()
    # Hilangkan 'km'
    last_part = last_part.replace('km', '').strip()
    # Hilangkan spasi
    last_part = last_part.replace(' ', '')

    # Jika mengandung 'k', hilangkan 'k' lalu multiply 1000
    # Contoh: '109k' -> '109' -> 109000
    #         '45k'  -> '45'  -> 45000
    if 'k' in last_part:
        last_part = last_part.replace('k', '')
        try:
            val = int(last_part)
            return val * 1000
        except:
            return None
    else:
        # Tanpa 'k', langsung parse integer
        try:
            return int(last_part)
        except:
            return None

@shared_task
def sync_mudahmy_to_main():
    """
    Mengambil seluruh data dari DB 'mudahmy_db' (model CarMudahMy),
    lalu melakukan upsert (update or create) ke DB utama (model Car).
    Kolom 'price' dan 'millage' dikonversi menjadi integer.
    'source' diset 'mudahmy'.
    Setelah selesai, kirim notifikasi WebSocket ke group "sync_updates".
    """
    qs = CarMudahMy.objects.using('mudahmy_db').all()
    processed_count = 0

    for row in qs.iterator(chunk_size=1000):
        # Konversi price dan millage
        price_int = parse_price(row.price)
        millage_int = parse_millage(row.millage)
        year_int = row.year if row.year else None

        # Data MudahMy disimpan apa adanya
        Car.objects.update_or_create(
            listing_url=row.listing_url,
            defaults={
                "brand": row.brand,
                "model": row.model,
                "variant": row.variant,
                "informasi_iklan": getattr(row, 'informasi_iklan', None),
                "lokasi": getattr(row, 'lokasi', None),
                "price": price_int,
                "year": year_int,
                "millage": millage_int,
                "transmission": row.transmission,
                "seat_capacity": row.seat_capacity if row.seat_capacity else None,
                "gambar": row.gambar,  
                "last_scraped_at": row.last_scraped_at,
                "version": row.version if row.version else 1,
                "source": "mudahmy"
            }
        )
        processed_count += 1

    # Kirim notifikasi ke group "sync_updates" via Channels
    message = f"Sync MudahMy selesai. Total diproses: {processed_count}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "sync_updates",
        {
            "type": "sync_update",
            "message": message
        }
    )

    return message

@shared_task
def sync_carlistmy_to_main():
    """
    Mengambil seluruh data dari DB 'carlistmy_db' (model CarCarlistMy),
    lalu melakukan upsert (update or create) ke DB utama (model Car).
    Kolom 'price' dan 'millage' dikonversi menjadi integer.
    'source' diset 'carlistmy'.
    Untuk kolom brand, model, variant: disimpan dalam bentuk huruf kapital (upper).
    Setelah selesai, kirim notifikasi WebSocket ke group "sync_updates".
    """
    qs = CarCarlistMy.objects.using('carlistmy_db').all()
    processed_count = 0

    for row in qs.iterator(chunk_size=1000):
        price_int = parse_price(row.price)
        millage_int = parse_millage(row.millage)
        year_int = row.year if row.year else None

        # Kolom brand, model, variant diubah menjadi uppercase
        brand_upper = row.brand.upper() if row.brand else None
        model_upper = row.model.upper() if row.model else None
        variant_upper = row.variant.upper() if row.variant else None

        Car.objects.update_or_create(
            listing_url=row.listing_url,
            defaults={
                "brand": brand_upper,
                "model": model_upper,
                "variant": variant_upper,
                "informasi_iklan": getattr(row, 'informasi_iklan', None),
                "lokasi": getattr(row, 'lokasi', None),
                "price": price_int,
                "year": year_int,
                "millage": millage_int,
                "transmission": row.transmission,
                "seat_capacity": row.seat_capacity if row.seat_capacity else None,
                "gambar": row.gambar,
                "last_scraped_at": row.last_scraped_at,
                "version": row.version if row.version else 1,
                "source": "carlistmy"
            }
        )
        processed_count += 1

    # Kirim notifikasi ke group "sync_updates" via Channels
    message = f"Sync CarlistMy selesai. Total diproses: {processed_count}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "sync_updates",
        {
            "type": "sync_update",
            "message": message
        }
    )

    return message
