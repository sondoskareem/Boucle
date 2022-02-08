from array import array
import random
import string
from typing import List

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Address, Product, Category, Item, Order, OrderStatus, Rating
from commerce.schemas import AddressSchema, AddressesOut, CheckoutSchema,CategoryOut, ProductOut, CitiesOut, CitySchema, ItemOut, ItemSchema, ItemCreate, RatingSchema
from config.utils.schemas import MessageOut

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
address_controller = Router(tags=['addresses'])
order_controller = Router(tags=['orders'])
user_controller = Router(tags=['users'])
category_controller = Router(tags=['categories'])
rating_controller = Router(tags=['rating'])

User = get_user_model()

# @user_controller.get('/users')
# def list_users(request):
#     user = User.objects.all().values()
#     return JsonResponse({"Users": list(user)})


# (todo)sending array of categories as filter to return matching products
@products_controller.get('',response={
    200: List[ProductOut],
    404: MessageOut
})
def list_products(
        request,
        *,
        q: str = None,
        price_from: int = None,
        price_to: int = None,
        categories = None,
):
    products_qs = Product.objects.filter(is_active=True).prefetch_related('category')

    if not products_qs:
        return 404, {'detail': 'No products found'}

    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    if price_from:
        products_qs = products_qs.filter(discounted_price__gte=price_from)

    if price_to:
        products_qs = products_qs.filter(discounted_price__lte=price_to)

    
    

    return products_qs


@products_controller.get('/{id}',auth=GlobalAuth(), response={
    200: ProductOut,
    404: MessageOut
})
def retrieve_product(request, id: UUID4):
    return get_object_or_404(Product, id=id)


@address_controller.get('' ,auth=GlobalAuth())
def list_addresses(request):
    pass


@category_controller.get('categories', response=List[CategoryOut])
def list_categories(request):
    return Category.objects.all()


@order_controller.get('cart',auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    user = get_object_or_404(User, id=request.auth['pk'])
    cart_items = Item.objects.filter(user=user, ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart',auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    try:
        user = get_object_or_404(User, id=request.auth['pk'])

        item = Item.objects.get(product_id=item_in.product_id, user=user)
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=User.objects.first())

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity',auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])

    item = get_object_or_404(Item, id=id, user=user)
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.delete('item/{id}',auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])

    item = get_object_or_404(Item, id=id, user=user)
    item.delete()

    return 204, {'detail': 'Item deleted!'}


def generate_ref_code():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


@order_controller.post('create-order', auth=GlobalAuth(), response=MessageOut)
def create_order(request):
    '''
    * add items and mark (ordered) field as True
    * add ref_number
    * add NEW status
    * calculate the total
    '''
    user = get_object_or_404(User, id=request.auth['pk'])

    order_qs = Order.objects.create(
        user=user,
        status=OrderStatus.objects.get(is_default=True),
        ref_code=generate_ref_code(),
        ordered=False,
    )

    user_items = Item.objects.filter(user=user).filter(ordered=False)

    order_qs.items.add(*user_items)
    order_qs.total = order_qs.order_total
    user_items.update(ordered=True)
    order_qs.save()

    return {'detail': 'order created successfully'}


############ Adresses CRUD
@order_controller.post('/item/{id}/increase-quantity',auth=GlobalAuth(), response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])

    item = get_object_or_404(Item, id=id, user=user)
    item.item_qty += 1
    item.save()

    return 200, {'detail': 'Item quantity increased successfully!'}



@order_controller.put('/checkout/{id}',auth=GlobalAuth(), response=MessageOut)
def checkout(request, id: UUID4, checkout_in: CheckoutSchema):
    order = get_object_or_404(Order, id=id)
    for key, value in checkout_in:
        setattr(order, key, value)
    return {'detail': 'order checkout successfully'}


@address_controller.get('addresses', auth=GlobalAuth(),response={
    200: List[AddressesOut],
    404: MessageOut
})
def list_addresses(request):
    addresses_qs = Address.objects.all()

    if addresses_qs:
        return addresses_qs

    return 404, {'detail': 'No addresses found'}


@address_controller.get('addresses/{id}',auth=GlobalAuth(), response={
    200: AddressesOut,
    404: MessageOut
})
def retrieve_address(request, id: UUID4):
    return get_object_or_404(Address, id=id)


@address_controller.post('addresses', auth=GlobalAuth(),response={
   200: MessageOut,
    400: MessageOut
})
def create_address(request, address_in: AddressSchema):
    user = get_object_or_404(User, id=request.auth['pk'])

    Address.objects.create(**address_in.dict() , user=user)
    return 200, {'detail': 'Added successfully'}


@address_controller.put('addresses/{id}',auth=GlobalAuth(), response={
    200: AddressSchema,
    400: MessageOut
})
def update_address(request, id: UUID4, address_in: AddressSchema):
    address = get_object_or_404(Address, id=id)
    for key, value in address_in:
        setattr(address, key, value)
    return 200, address


@address_controller.delete('addresses/{id}', auth=GlobalAuth(),response={
    204: MessageOut
})
def delete_address(request, id: UUID4):
    address = get_object_or_404(Address, id=id)
    address.delete()
    return 204, {'detail': ''}



@rating_controller.post('rating',auth=GlobalAuth(), response={
    200: MessageOut,
})
def rating(request, rating_in: RatingSchema):
    user = get_object_or_404(User, id=request.auth['pk'])

    Rating.objects.create(**rating_in.dict() , user=user)
    return 200, {'detail': 'Added successfully'}
