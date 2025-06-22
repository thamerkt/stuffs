from rest_framework import serializers
from .models import (
    Stuff, Category, StuffManagement, Review, EquipmentImage, test,
    Visitor, ItemView, CartActivity, Rental,
    SiteStat, TrafficSource, DeviceStat, CategoryStat,Favorite
)
import re
from django.http import QueryDict

class ReviewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
class WishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = test
        fields = '__all__'

class EquipmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentImage
        fields = ['id', 'stuff', 'url', 'alt', 'position']
class StuffManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StuffManagement
        fields = '__all__'
class StuffSerializer(serializers.ModelSerializer):
    stuff_management = StuffManagementSerializer(required=False)
    equipment_images = EquipmentImageSerializer(many=True, required=False)

    class Meta:
        model = Stuff
        fields = '__all__'

    def to_internal_value(self, data):
        if isinstance(data, QueryDict):
            formatted_data = {}
            management_data = {}
            image_meta_data = []

            for key in data.keys():
                if key.startswith('stuff_management['):
                    field_name = key.split('[')[1].rstrip(']')
                    management_data[field_name] = data.get(key)
                elif key.startswith('equipment_images['):
                    match = re.match(r'equipment_images\[(\d+)]\[(\w+)]', key)
                    if match:
                        idx, field = int(match.group(1)), match.group(2)
                        while len(image_meta_data) <= idx:
                            image_meta_data.append({})
                        image_meta_data[idx][field] = data.get(key)
                else:
                    formatted_data[key] = data.get(key)

            if management_data:
                formatted_data['stuff_management'] = management_data
            if image_meta_data:
                self.context['image_meta_data'] = image_meta_data

            return super().to_internal_value(formatted_data)

        return super().to_internal_value(data)

    def create(self, validated_data):
        request = self.context.get('request')
        management_data = validated_data.pop('stuff_management', None)
        image_meta = self.context.get('image_meta_data', [])

        # Create StuffManagement
        stuff_management = None
        if management_data:
            contract_file = request.FILES.get('stuff_management[contract_required]')
            if contract_file:
                management_data['contract_required'] = contract_file
            stuff_management = StuffManagement.objects.create(**management_data)

        # Create Stuff
        stuff = Stuff.objects.create(stuff_management=stuff_management, **validated_data)

        # Loop through all FILES and match with metadata
        image_files = []
        for key, file in request.FILES.items():
            if key.startswith('equipment_images[') and key.endswith('][url]'):
                match = re.match(r'equipment_images\[(\d+)]\[url\]', key)
                if match:
                    idx = int(match.group(1))
                    meta = image_meta[idx] if idx < len(image_meta) else {}
                    EquipmentImage.objects.create(
                        stuff=stuff,
                        url=file,
                        alt=meta.get('alt', f"Image {idx+1}"),
                        position=int(meta.get('position', idx))
                    )

        return stuff
    def update(self, instance, validated_data):
        request = self.context.get('request')
        management_data = validated_data.pop('stuff_management', None)
        image_meta = self.context.get('image_meta_data', [])

        # Update StuffManagement if provided
        if management_data:
            contract_file = request.FILES.get('stuff_management[contract_required]')
            if contract_file:
                management_data['contract_required'] = contract_file

            if instance.stuff_management:
                for attr, value in management_data.items():
                    setattr(instance.stuff_management, attr, value)
                instance.stuff_management.save()
            else:
                instance.stuff_management = StuffManagement.objects.create(**management_data)

        # Update basic fields of Stuff
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or replace EquipmentImages if new ones are provided
        if request.FILES:
            # Optionally clear existing images if you want full replacement
            instance.equipment_images.all().delete()

            for key, file in request.FILES.items():
                if key.startswith('equipment_images[') and key.endswith('][url]'):
                    match = re.match(r'equipment_images\[(\d+)]\[url\]', key)
                    if match:
                        idx = int(match.group(1))
                        meta = image_meta[idx] if idx < len(image_meta) else {}
                        EquipmentImage.objects.create(
                            stuff=instance,
                            url=file,
                            alt=meta.get('alt', f"Image {idx+1}"),
                            position=int(meta.get('position', idx))
                        )

        return instance


# ======================= New Serializers =======================

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = '__all__'
        read_only_fields = ('first_visit', 'last_visit')

class ItemViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemView
        fields = '__all__'
        read_only_fields = ('timestamp',)

class CartActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CartActivity
        fields = '__all__'
        read_only_fields = ('timestamp',)

    


class RentalSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Rental
        fields = '__all__'

class SiteStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteStat
        fields = '__all__'

class TrafficSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSource
        fields = '__all__'

class DeviceStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStat
        fields = '__all__'

class CategoryStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryStat
        fields = '__all__'
