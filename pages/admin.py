from django.contrib import admin
from .models import Trip, Item, Profile

# Inline model to display related Items within the Trip view
class ItemInline(admin.TabularInline):
    model = Item
    extra = 1  # Number of empty item forms shown

# Admin class for the Trip model
class TripAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'leader', 'code')
    search_fields = ('title', 'code', 'leader__username')
    list_filter = ('date', 'leader')  
    inlines = [ItemInline]
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'


# Register Trip model with the customized TripAdmin class
admin.site.register(Trip, TripAdmin)

# You can also register the Item model directly if you need a separate view for items
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'trip', 'is_paid')
    search_fields = ('name', 'trip__title')

admin.site.register(Item, ItemAdmin)

# Admin class for the Profile model
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('iban', 'user', 'bank_name')


# Register Profile model with the customized ProfileAdmin class
admin.site.register(Profile, ProfileAdmin)
