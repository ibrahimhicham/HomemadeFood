# Dish Varieties/Sections Feature Implementation Plan

## Overview
This document outlines the plan for implementing dish varieties/sections functionality in the Homemade Food Authentication Service. This feature will allow chefs to add sections of varieties (such as sizes: small, medium, large) when creating dishes.

## Current State
Currently, the dishes app supports:
- Categories
- Dishes with basic information (name, description, price, etc.)
- Dish reviews
- Dish images

However, there is no functionality for dish variations or customizable options.

## Proposed Solution
We will implement a flexible system that allows chefs to define sections of varieties for their dishes. Each section can contain multiple options with different prices.

### Key Requirements
1. **Dish-Specific Varieties**: Each variety section and its options will be associated with only one dish. Every dish will have its own unique set of varieties.
2. **Creator Permissions**: Only the chef who created a dish will be authorized to create, update, or delete varieties for that dish.
3. **User Access**: Regular users will have read-only access to view varieties when browsing dishes. They can optionally select from available varieties when adding a dish to their order, but selection will not be mandatory.

## Implementation Details

### 1. New Models

#### DishVarietySection Model
Represents a section of varieties for a dish (e.g., "Size Options", "Toppings", "Spice Level").

```python
class DishVarietySection(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='variety_sections')
    name = models.CharField(max_length=100)  # e.g., "Size Options"
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)  # Whether customer must select an option

    def __str__(self):
        return f"{self.name} for {self.dish.name}"
```

#### DishVarietyOption Model
Represents individual options within a section (e.g., "Small", "Medium", "Large") with potential price adjustments.

```python
class DishVarietyOption(models.Model):
    section = models.ForeignKey(DishVarietySection, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)  # e.g., "Small"
    price_adjustment = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # Additional cost
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.section.name})"
```

### 2. Updated Models
The existing `Dish` model will remain largely unchanged, but will gain relationships to the new variety models through the foreign keys defined above.

### 3. Serializers

#### DishVarietySectionSerializer
```python
class DishVarietySectionSerializer(serializers.ModelSerializer):
    options = DishVarietyOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DishVarietySection
        fields = ['id', 'name', 'description', 'is_required', 'options']
        read_only_fields = ['id']
```

#### DishVarietyOptionSerializer
```python
class DishVarietyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishVarietyOption
        fields = ['id', 'name', 'price_adjustment', 'is_available']
        read_only_fields = ['id']
```

#### Updated DishSerializer
Modify the existing `DishSerializer` to include variety sections:
```python
class DishSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    variety_sections = DishVarietySectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dish
        fields = [
            # ... existing fields ...
            'variety_sections',
        ]
        # ... existing configuration ...
```

### 4. Views
Add new views or modify existing ones to handle CRUD operations for dish varieties with proper permission controls:

#### DishVarietySection Views
- `DishVarietySectionCreateView`: Create new variety sections for a dish (only dish creator can access)
- `DishVarietySectionUpdateView`: Update existing variety sections (only dish creator can access)
- `DishVarietySectionDeleteView`: Delete variety sections (only dish creator can access)

#### DishVarietyOption Views
- `DishVarietyOptionCreateView`: Create new variety options within a section (only dish creator can access)
- `DishVarietyOptionUpdateView`: Update existing variety options (only dish creator can access)
- `DishVarietyOptionDeleteView`: Delete variety options (only dish creator can access)

### 5. Admin Interface
Register the new models in the admin panel with appropriate configurations:

```python
@admin.register(DishVarietySection)
class DishVarietySectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'dish', 'is_required')
    list_filter = ('is_required',)
    search_fields = ('name', 'dish__name')

@admin.register(DishVarietyOption)
class DishVarietyOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'price_adjustment', 'is_available')
    list_filter = ('is_available', 'section')
    search_fields = ('name', 'section__name')
```

### 6. Database Migrations
Create and run database migrations to add the new tables:
- `dishes_dishvarietysection`
- `dishes_dishvarietyoption`

### 7. API Endpoints
Add new API endpoints to manage dish varieties with appropriate permissions:

```
POST /api/dishes/{dish_id}/sections/          # Create a new variety section (chef only)
GET /api/dishes/{dish_id}/sections/           # List all sections for a dish (public read-only)
PUT /api/dishes/{dish_id}/sections/{id}/      # Update a specific section (dish creator only)
DELETE /api/dishes/{dish_id}/sections/{id}/   # Delete a specific section (dish creator only)

POST /api/dishes/sections/{section_id}/options/    # Create a new variety option (chef only)
GET /api/dishes/sections/{section_id}/options/     # List all options in a section (public read-only)
PUT /api/dishes/sections/{section_id}/options/{id}/   # Update a specific option (dish creator only)
DELETE /api/dishes/sections/{section_id}/options/{id}/ # Delete a specific option (dish creator only)
```

### 8. Frontend Integration
The frontend will need to be updated to:
- Display available variety sections and options when viewing a dish (read-only for customers)
- Allow customers to optionally select from available varieties when adding a dish to their cart
- Calculate the final price based on selected options
- Enable customers to add dishes to their cart without selecting any varieties (varieties are optional)

### 9. Testing
Add comprehensive test coverage for:
- Model validation and relationships
- Serializer functionality
- View behavior and permissions (ensuring only dish creators can modify varieties)
- API endpoint functionality with proper authentication checks
- Customer read-only access to varieties
- Optional variety selection in orders
- Edge cases (required sections, unavailable options, etc.)

## Benefits of This Approach
1. **Dish-Specific Customization**: Each dish has its own unique set of varieties, allowing for tailored customization options per dish
2. **Permission Control**: Only dish creators can manage their dish's varieties, ensuring proper ownership and control
3. **Flexible User Experience**: Customers can optionally select varieties when ordering, or skip them entirely
4. **Scalability**: Easy to add new sections and options without changing core models
5. **Maintainability**: Clear separation between dish and variety data

## Potential Challenges
1. **Price Calculation**: Need to properly handle price adjustments based on selected options
2. **Permission Validation**: Ensuring only dish creators can modify their dish's varieties
3. **UI Complexity**: Frontend will need to handle complex selection interfaces
4. **Order Processing**: Handling orders with and without variety selections appropriately

## Timeline
- Phase 1: Implement models and migrations (2 days)
- Phase 2: Create serializers and views (3 days)
- Phase 3: Add admin interface and API endpoints (2 days)
- Phase 4: Write tests and documentation (2 days)
- Phase 5: Integrate with frontend (timeline varies based on frontend complexity)