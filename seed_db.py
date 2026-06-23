import os
import sys
import shutil
import django
from decimal import Decimal

# Add current directory to path and setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mtkf_perfumes.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Brand, Category, Product

def seed():
    print("Seeding database...")
    
    # 1. Create Superuser (Admin)
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@mtkf.com', 'adminpassword')
        print("Superuser 'admin' created with password 'adminpassword'")
    else:
        print("Superuser 'admin' already exists.")

    # 2. Setup Media Folders
    media_products_dir = os.path.join('media', 'products')
    os.makedirs(media_products_dir, exist_ok=True)
    
    # Source image paths from brain directory
    brain_dir = r"C:\Users\Ameeynerh\.gemini\antigravity\brain\642f34b7-6016-4499-a52c-8f2628134b52"
    
    images_mapping = {
        'bleu_de_chanel.png': os.path.join(brain_dir, 'bleu_de_chanel_1782240290996.png'),
        'creed_aventus.png': os.path.join(brain_dir, 'creed_aventus_1782240315331.png'),
        'tom_ford_oud.png': os.path.join(brain_dir, 'tom_ford_oud_1782240338242.png'),
        'dior_sauvage.png': os.path.join(brain_dir, 'dior_sauvage_1782240365949.png'),
    }

    # Copy files
    for filename, src in images_mapping.items():
        dst = os.path.join(media_products_dir, filename)
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Copied {src} to {dst}")
        else:
            print(f"Source file not found: {src}")

    # 3. Create Brands
    chanel, _ = Brand.objects.get_or_create(name='Chanel', defaults={'description': 'House of Chanel, founded in 1910 by Coco Chanel.'})
    creed, _ = Brand.objects.get_or_create(name='Creed', defaults={'description': 'The House of Creed is a multi-national perfume house.'})
    tom_ford, _ = Brand.objects.get_or_create(name='Tom Ford', defaults={'description': 'Luxury brand founded by designer Tom Ford in 2005.'})
    dior, _ = Brand.objects.get_or_create(name='Dior', defaults={'description': 'Christian Dior SE, commonly known as Dior, is a French luxury goods company.'})
    print("Brands created.")

    # 4. Create Categories
    edp, _ = Category.objects.get_or_create(name='Eau de Parfum')
    edt, _ = Category.objects.get_or_create(name='Eau de Toilette')
    cologne, _ = Category.objects.get_or_create(name='Cologne')
    print("Categories created.")

    # 5. Create Products
    products_data = [
        {
            'name': 'Bleu de Chanel',
            'description': 'A woody, aromatic fragrance for the free and independent man. Captivating, timeless scent in a deep blue bottle.',
            'price': Decimal('145.00'),
            'brand': chanel,
            'category': edp,
            'image': 'products/bleu_de_chanel.png',
            'stock': 15
        },
        {
            'name': 'Aventus',
            'description': 'The exceptional Aventus features notes of blackcurrant, bergamot, apple, birch, patchouli, jasmine, and oakmoss.',
            'price': Decimal('350.00'),
            'brand': creed,
            'category': cologne,
            'image': 'products/creed_aventus.png',
            'stock': 8
        },
        {
            'name': 'Oud Wood',
            'description': 'One of the most rare, precious, and expensive ingredients in a perfumer\'s arsenal, Tom Ford Oud Wood is a dark and smoky composition.',
            'price': Decimal('285.00'),
            'brand': tom_ford,
            'category': edp,
            'image': 'products/tom_ford_oud.png',
            'stock': 12
        },
        {
            'name': 'Sauvage',
            'description': 'A radically fresh composition, dictated by a name that has the ring of a manifesto. Raw and noble all at once, with fresh bergamot and wood.',
            'price': Decimal('120.00'),
            'brand': dior,
            'category': edt,
            'image': 'products/dior_sauvage.png',
            'stock': 20
        }
    ]

    for p_info in products_data:
        prod, created = Product.objects.get_or_create(
            name=p_info['name'],
            defaults={
                'description': p_info['description'],
                'price': p_info['price'],
                'brand': p_info['brand'],
                'category': p_info['category'],
                'image': p_info['image'],
                'stock': p_info['stock']
            }
        )
        if created:
            print(f"Product '{prod.name}' created.")
        else:
            print(f"Product '{prod.name}' already exists.")

    print("Seeding complete.")

if __name__ == '__main__':
    seed()
