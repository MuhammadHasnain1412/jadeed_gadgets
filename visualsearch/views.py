from django.shortcuts import render

# Create your views here.
import os
import numpy as np
from django.shortcuts import render
from django.core.files.storage import default_storage
from products.models import Product
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity

# Load model only once
model = ResNet50(weights='imagenet', include_top=False, pooling='avg')

def extract_features(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return model.predict(img_array)

def visual_search(request):
    if request.method == 'POST' and request.FILES.get('query_image'):
        query_img = request.FILES['query_image']
        path = default_storage.save('query/' + query_img.name, query_img)
        full_path = os.path.join('media', path)

        query_features = extract_features(full_path)

        results = []
        for product in Product.objects.all():
            if product.image:
                product_img_path = os.path.join('media', str(product.image))
                product_features = extract_features(product_img_path)
                similarity = cosine_similarity(query_features, product_features)[0][0]
                results.append((product, similarity))

        # Sort by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        top_matches = [product for product, score in results[:5]]

        return render(request, 'visualsearch/visualsearch_result.html', {'products': top_matches})

    return render(request, 'visualsearch/visualsearch_form.html')
