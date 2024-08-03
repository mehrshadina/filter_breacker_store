from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
import requests
from .models import Product, Order, UserProfile

def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        if 'message' in payload:
            chat_id = payload['message']['chat']['id']
            text = payload['message']['text']
            user_data = {
                'first_name': payload['message']['chat'].get('first_name'),
                'last_name': payload['message']['chat'].get('last_name'),
                'username': payload['message']['chat'].get('username'),
            }
            handle_message(chat_id, text, user_data)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def handle_message(chat_id, text, user_data):
    user = create_user(chat_id, user_data)
    if text.lower() == '/start':
        response_text = f"Welcome {user.username}! Use /products to see our products."
    elif text.lower() == '/products':
        products = Product.objects.all()
        response_text = "\n".join([f"{p.id}. {p.name} - ${p.price}" for p in products])
    elif text.startswith('/order'):
        try:
            _, product_id, quantity = text.split()
            product = Product.objects.get(id=product_id)
            quantity = int(quantity)
            total_price = product.price * quantity
            order = Order.objects.create(product=product, quantity=quantity, total_price=total_price, user_telegram_id=chat_id)
            response_text = f"Order placed! Total price: ${total_price}"
        except Exception as e:
            response_text = "Failed to place order. Make sure the product ID and quantity are correct."
    else:
        response_text = "Invalid command."
    send_telegram_message(chat_id, response_text)

def create_user(telegram_id, user_data):
    username = f"user_{telegram_id}"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create(username=username, password=telegram_id)
        user_profile = UserProfile.objects.create(user=user, telegram_id=telegram_id, first_name=user_data.get('first_name'), last_name=user_data.get('last_name'), username=user_data.get('username'))
        return user
    return User.objects.get(username=username)

def send_telegram_message(chat_id, text):
    BOT_TOKEN = '2007984789:AAH5B5b1-aEPD9qPnIJUde6-ENkpg0BcKHI'
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    requests.post(url, json=payload)
