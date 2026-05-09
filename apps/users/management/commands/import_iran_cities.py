import json
import os
from django.core.management.base import BaseCommand
from apps.users.models import Province, City


class Command(BaseCommand):
    help = 'Import Iranian provinces and cities from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='iran_cities.json',
            help='Path to JSON file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        # Clear existing data
        City.objects.all().delete()
        Province.objects.all().delete()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cache provinces to avoid repeated queries
        provinces_cache = {}
        cities_count = 0
        
        for item in data:
            province_id = item.get('provinceId', '').strip()
            province_name = item.get('provinceName', '').strip()
            city_id = item.get('cityId', '').strip()
            city_name = item.get('cityName', '').strip()
            
            if not all([province_id, province_name, city_id, city_name]):
                continue
            
            # Get or create province
            if province_id not in provinces_cache:
                province, created = Province.objects.get_or_create(
                    province_id=province_id,
                    defaults={'name': province_name}
                )
                provinces_cache[province_id] = province
                if created:
                    self.stdout.write(f"Added province: {province_name}")
            
            province = provinces_cache[province_id]
            
            # Create city
            city, created = City.objects.get_or_create(
                city_id=city_id,
                province=province,
                defaults={'name': city_name}
            )
            
            if created:
                cities_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {len(provinces_cache)} provinces '
                f'and {cities_count} cities.'
            )
        )