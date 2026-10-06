from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.users.models import User
from apps.users.db.province_model import Province
from apps.users.db.city_model import City


class DiscoverQuerySerializer(serializers.Serializer):
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=False)
    min_age = serializers.IntegerField(min_value=0, required=False)
    max_age = serializers.IntegerField(min_value=0, required=False)
    province_id = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), required=False)
    city_id = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), required=False)
    location = serializers.CharField(max_length=100, required=False, allow_blank=False, trim_whitespace=True)
    page = serializers.IntegerField(min_value=1, required=False, default=1)

    def validate(self, attrs):
        if attrs.get('min_age') is not None and attrs.get('max_age') is not None:
            if attrs['min_age'] > attrs['max_age']:
                raise serializers.ValidationError({
                    'max_age': "Maximum age must be greater than or equal to minimum age."
                })
        if attrs.get('city_id') and attrs.get('province_id'):
            if attrs['city_id'].province_id != attrs['province_id'].pk:
                raise serializers.ValidationError({
                    'city_id': "The selected city does not belong to the selected province."
                })
        return attrs


class SaveSuggestionsSerializer(serializers.Serializer):
    profile_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=20,
        help_text="User IDs returned in the current Discover page.",
    )

    def validate_profile_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Profile IDs must not contain duplicates.")
        return value


class SaveSuggestionsResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    saved_count = serializers.IntegerField()
    profile_ids = serializers.ListField(child=serializers.IntegerField())


class ProfileCardSerializer(serializers.ModelSerializer):
    """
    Serializer for profile cards shown in Discover.
    Contains only public information needed for swiping.
    """
    interests = serializers.SerializerMethodField()
    province_name = serializers.CharField(source='province.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name', 
            'age',
            'gender',
            'city_name',
            'province_name',
            'bio',
            'profile_picture',
            'interests',
            'is_online',
        ]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_interests(self, obj):
        user_interests = obj.userinterest_set.all().select_related('interest')
        return [ui.interest.name for ui in user_interests]
