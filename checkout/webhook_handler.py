from django.http import HttpResponse

from .models import Order, OrderItem
from menu.models import Product

import json
import time

class Stripe_Web_Hook_Handler:
    """Handle Stripe webhooks"""

    def __init__(self, request):
        self.request = request

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook from Stripe
        """
        intent = event.data.object
        pid = intent.id
        cart = intent.metadata.cart
        save_info = intent.metadata.save_info
        billing_details = intent.charges.data[0].billing_details
        shipping_details = intent.shipping
        order_total = round(intent.data.charges[0].amount / 100, 2)

        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        order_exists = False

        attempt = 1
        while attempt <= 5:
            try:
                order = Order.objects.get(
                    full_name__iexact = shipping_details.name,
                    email__iexact = billing_details.email,
                    phone_number__iexact = shipping_details.phone,
                    postcode__iexact = shipping_details.address.postal_code,
                    town_or_city__iexact = shipping_details.address.city,
                    street_address1__iexact = shipping_details.address.line1,
                    street_address2__iexact = shipping_details.address.line2,
                    order_total = order_total,
                    original_cart = cart,
                    stripe_pid = pid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)
        if order_exists:
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | SUCCESS: Verified order already in database',
                status=200)
        else:
            order = None
            try:
                order = Order.objects.create(
                    full_name = shipping_details.name,
                    email = billing_details.email,
                    phone_number = shipping_details.phone,
                    postcode = shipping_details.address.postal_code,
                    town_or_city = shipping_details.address.city,
                    street_address1 = shipping_details.address.line1,
                    street_address2 = shipping_details.address.line2,
                    original_cart = cart,
                    stripe_pid = pid,
                )
                for item_id, item_data in json.loads(cart).items():
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_item = OrderItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_item.save()
            except Exception as e:
                if order:
                    order.delete()
                return HttpResponse(
                    content=f'Webhook received: {event["type"]} | ERROR: {e}',
                    status=500)
        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS: Created order in webhook',
            status=200)

    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)