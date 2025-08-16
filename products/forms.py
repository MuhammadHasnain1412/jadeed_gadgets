from django import forms
from django.db.models import Q
from .models import Product, Store

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'brand', 'price', 'stock', 'ram', 'processor', 'storage', 'screen_size', 'image', 'category', 'tags', 'is_featured', 'is_flash_sale', 'flash_sale_end']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product Description'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity in Stock'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated tags (e.g., gaming, wireless, bluetooth)'}),
            'ram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 8GB, 16GB'}),
            'processor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Intel Core i5, AMD Ryzen'}),
            'storage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 256GB SSD, 1TB HDD'}),
            'screen_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 15.6 inch'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_flash_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'flash_sale_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'description', 'logo', 'banner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Store Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Store Description'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'banner': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class ProductFilterForm(forms.Form):
    CATEGORY_CHOICES = [('', 'All Categories')] + Product.CATEGORY_CHOICES
    SORT_CHOICES = [
        ('name', 'Name (A-Z)'),
        ('-name', 'Name (Z-A)'),
        ('price', 'Price (Low to High)'),
        ('-price', 'Price (High to Low)'),
        ('-created_at', 'Latest'),
        ('created_at', 'Oldest'),
        ('-rating', 'Highest Rated'),
        ('-review_count', 'Most Reviewed'),
    ]
    
    # Search field
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Search by name, brand, specs...',
            'id': 'search-input'
        })
    )
    
    # Category filter
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Brand filter (will be populated dynamically)
    brand = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Brand name...',
            'list': 'brand-list'
        })
    )
    
    # Price range filters
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Min Price',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Max Price',
            'step': '0.01'
        })
    )
    
    # RAM filter
    ram = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'RAM (e.g., 8GB)',
            'list': 'ram-list'
        })
    )
    
    # Processor filter
    processor = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Processor...',
            'list': 'processor-list'
        })
    )
    
    # Rating filter
    min_rating = forms.ChoiceField(
        choices=[
            ('', 'Any Rating'),
            ('1', '1+ Stars'),
            ('2', '2+ Stars'),
            ('3', '3+ Stars'),
            ('4', '4+ Stars'),
            ('5', '5 Stars'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Availability filter
    in_stock_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Featured products only
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Flash sale products only
    flash_sale_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Sort by
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate dynamic choices from database
        self.populate_dynamic_choices()
    
    def populate_dynamic_choices(self):
        """Populate brand and other dynamic filter options"""
        # Get unique brands from active products
        brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().order_by('brand')
        self.brand_list = [brand for brand in brands if brand]
        
        # Get unique RAM options
        rams = Product.objects.filter(is_active=True, ram__isnull=False).exclude(ram='').values_list('ram', flat=True).distinct().order_by('ram')
        self.ram_list = [ram for ram in rams if ram]
        
        # Get unique processors
        processors = Product.objects.filter(is_active=True, processor__isnull=False).exclude(processor='').values_list('processor', flat=True).distinct().order_by('processor')
        self.processor_list = [processor for processor in processors if processor]
