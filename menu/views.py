from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.functions import Lower

from .models import Product, Category
from .forms import ProductForm
from images.models import Image, Page

def menu(request):

    menu = Product.objects.all()
    categories = None
    query = None

    if request.GET:
        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            menu = menu.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You didn't enter any search criteria!")
                return redirect(reverse('products'))
            
            queries = Q(name__icontains=query) | Q(description__icontains=query)
            menu = menu.filter(queries)

    context = {
        'menu': menu,
        'categories': categories,
        'query': query,
    }

    return render(request, 'menu/menu.html', context)

@login_required
def add_product(request):
    """Add a product to the store"""

    if not request.user.is_superuser:
        messages.info(request, 'Oops! You don\'t have the required permission to access this page. Login with the required credentials to do so!')
        return redirect(reverse('home'))

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Successfully added product!')
            return redirect(reverse('add-product'))
        else:
            messages.error(request, 'Failed to add product. Please ensure the form is valid.')
    else:
        form = ProductForm()
    
    images = Image.objects.all()
    add_product_header = images.filter(image_name__icontains='add-product-header')[0]
    template = 'menu/add-product.html'
    context = {
        'form': form,
        'add_product_header': add_product_header,
    }

    return render(request, template, context)

@login_required
def edit_product(request, product_id):
    """ Edit a product on the menu """
    if not request.user.is_superuser:
        messages.info(request, 'Oops! You don\'t have the required permission to access this page. Login with the required credentials to do so!')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect(reverse('menu'))
        else:
            messages.error(request, 'Failed to update product. Please ensure the form is valid.')
    else:
        form = ProductForm(instance=product)
        messages.info(request, f'You are editing {product.name}')

    template = 'menu/edit-product.html'
    context = {
        'form': form,
        'product': product,
    }

    return render(request, template, context)

@login_required
def delete_product(request, product_id):
    """ Delete a product from the menu """
    if not request.user.is_superuser:
        messages.info(request, 'Oops! You don\'t have the required permission to access this page. Login with the required credentials to do so!')
        return redirect(reverse('home'))
        
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Product deleted!')
    
    return redirect(reverse('menu'))