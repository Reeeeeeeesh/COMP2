"""
Dynamic field selection mixin for DRF serializers.

This module provides a mixin that allows serializers to dynamically include
only specific fields requested by the client via the 'fields' query parameter.
"""

class DynamicFieldsMixin:
    """
    A serializer mixin that takes an additional `fields` parameter that controls
    which fields should be displayed.
    
    Usage:
        class MySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = ['id', 'name', 'description', ...]
                
    Client can request specific fields using the 'fields' query parameter:
        GET /api/mymodel/?fields=id,name
    """
    
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        
        if fields is not None and fields:
            # Drop any fields that are not specified in the `fields` argument
            allowed = set(fields.split(','))
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
