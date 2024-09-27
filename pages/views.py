from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User , auth
from django.contrib.auth.decorators import login_required
import random,string
from .models import Trip, Item, TripMember, Profile
from django.contrib import messages
from django.http import JsonResponse


# Create your views here.

def generate_unique_trip_code():
    length = 10
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Trip.objects.filter(code=code).exists():
            return code

@login_required(login_url='login')
def home(request):
    current_user = request.user
    Profile.objects.get_or_create(user=request.user)
    trips = Trip.objects.filter(participants=current_user)
    joined_trips = Trip.objects.filter(participants=current_user).exclude(leader=current_user).exists()
    created_trips = Trip.objects.filter(leader=current_user).exists()
    
    return render(request, 'pages/home.html', {
        'user'          : current_user,
        'trips'         : trips,
        'joined_trips'  : joined_trips,
        'created_trips' : created_trips

    })

def login(request):
    return render(request, 'pages/login.html')


def logout(request):
    auth.logout(request)
    return redirect('login')

@login_required(login_url='login')
def create_trip(request):
    if request.method == 'POST':
        current_user = request.user
        title = str(request.POST.get('title')) 
        date = request.POST.get('date')
        items = request.POST.getlist('items[]')
        quantities = request.POST.getlist('quantities[]')  # Get the quantities

        # Create the Trip instance
        trip = Trip.objects.create(
            title=title,
            date=date, 
            leader=current_user,
            code=generate_unique_trip_code()
        )
        trip.participants.add(current_user)
        TripMember.objects.create(trip=trip, member=current_user).save()

        trip.save()

        # Loop through items and quantities to create associated Item instances
        for item_name, quantity in zip(items, quantities):
            if item_name and quantity:
                # Ensure the item does not already exist for the trip
                if not Item.objects.filter(trip=trip, name=str(item_name)).exists():
                    Item.objects.create(
                        trip=trip,
                        name=str(item_name),
                        quantity=int(quantity)  # Add the quantity
                    )

        return redirect('home')

    return redirect('home')


@login_required(login_url='login')
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    if request.user == trip.leader: # Only allow leader to delete the trip
        
        if trip.has_ended and trip.confirmed_ratio() != 100:
            messages.error(request, 'You cannot delete a trip that has ended and not all members have confirmed payment!')
            return redirect('trip_details', trip_id=trip_id)



        trip.delete()
        return redirect('home')
    else:
        messages.error(request, 'You are not allowed to delete this trip!')
        return redirect('trip_details', trip_id=trip_id)

@login_required(login_url='login')
def trip_details(request, trip_id):
    
    trip = get_object_or_404(Trip, id=trip_id)
    total_paid = trip.total_amount_paid()
    complete_ratio = trip.complete_ratio()
    confirmed_ratio = trip.confirmed_ratio()
    split_bill = trip.split_bill()

    if request.user not in trip.participants.all():
        messages.error(request, 'You are not a participant in this trip!')
        return redirect('home')

    return render(request, 'pages/trip_details.html',
                   {'trip': trip,
                    'total_paid': total_paid,
                    'complete_ratio': complete_ratio,
                    'confirmed_ratio': confirmed_ratio,
                    'split_bill': split_bill,
                    'user': request.user,
                    'member': TripMember.objects.get(trip=trip, member=request.user),
                    })

@login_required(login_url='login')
def join_trip(request):
    if request.method == 'POST':
        trip_code = request.POST.get('trip_code').strip()
        current_user = request.user

        if not Trip.objects.filter(code=trip_code).exists():
            messages.error(request, 'The trip code you entered does not exist.')
            return redirect('home')
        trip = Trip.objects.get(code=trip_code)

        
        if trip.participants.filter(id=current_user.id).exists():
            messages.info(request, 'You are already a participant in this trip.')
            return redirect('home')

        trip.participants.add(current_user)
        TripMember.objects.create(trip=trip, member=current_user).save()

        trip.save()
        messages.success(request, 'You have successfully joined the trip!')
        return redirect('home')

    return redirect('home')


@login_required(login_url='login')
def pay_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        if item.is_paid:
            messages.error(request, 'Item is already paid!')
            return redirect('trip_details', trip_id=item.trip.id)
        amount_paid = request.POST.get('amount_paid')

        if request.user not in item.trip.participants.all():
            messages.error(request, 'You are not a participant in this trip!')
            return redirect('home')

        try:
            # Validate the amount paid
            amount_paid = float(amount_paid)
            item.is_paid = True
            item.payer = request.user  # Mark the payer as the current user
            item.amount_paid = amount_paid
            item.save()
            messages.success(request, 'The Item paid successfully!')
            return redirect('trip_details', trip_id=item.trip.id)
        except ValueError:
            messages.error(request, 'Invalid amount entered!')
            return redirect('trip_details', trip_id=item.trip.id)

    return redirect('trip_details', trip_id=item.trip.id)


@login_required
def add_item(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    if request.user not in trip.participants.all():
        messages.error(request, 'You are not a participant in this trip!')
        return redirect('home')
    
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        quantity = request.POST.get('quantity')

        # Create a new item for the trip
        Item.objects.create(
            trip=trip,
            name=item_name,
            quantity=quantity
        )
        messages.success(request, 'Item added successfully!')

        return redirect('trip_details', trip_id=trip_id)

    return redirect('trip_details', trip_id=trip_id)

@login_required(login_url='login')
def join_trip_by_code(request, trip_code):
    trip_code = trip_code.strip()
    trip = get_object_or_404(Trip, code=trip_code)
    if request.user in trip.participants.all():
        messages.info(request, 'You are already a participant in this trip.')
        return redirect('home')

    if request.method == 'POST' and 'yes' in request.POST:
        current_user = request.user        
        
        if trip.participants.filter(id=current_user.id).exists():
            messages.info(request, 'You are already a participant in this trip.')
            return redirect('home')

        trip.participants.add(current_user)
        TripMember.objects.create(trip=trip, member=current_user).save()
        trip.save()
        messages.success(request, 'You have successfully joined the trip!')
        return redirect('home')
    else:
        trip = Trip.objects.get(code=trip_code)
        return render(request, 'pages/join_trip_by_code.html', {'trip': trip})
    

@login_required(login_url='login')
def leave_trip(request, trip_id):
    current_user = request.user
    if current_user == Trip.objects.get(id=trip_id).leader:
        messages.error(request, 'You are the leader of this trip. You cannot leave the trip!')
        return redirect('trip_details', trip_id=trip_id)
    
    if current_user not in Trip.objects.get(id=trip_id).participants.all():
        messages.error(request, 'You are not a participant in this trip!')
        return redirect('home')

    trip = Trip.objects.get(id=trip_id)
    user = request.user
    trip.participants.remove(user)
    TripMember.objects.get(trip=trip, member=user).delete()
    messages.success(request, 'You have successfully left the trip!')
    return redirect('home') 


@login_required(login_url='login')
def get_trip_info(request, trip_code):
    trip_code = trip_code.strip()
    try:
        trip = Trip.objects.get(code=trip_code)
        data = {
            'success': True,
            'title': trip.title,
            'date': trip.date.strftime('%Y-%m-%d'),
            'leader': trip.leader.username,
            'trip_end': trip.has_ended,

        }
    except Trip.DoesNotExist:
        data = {'success': False}

    return JsonResponse(data)

def get_user_iban(request, user_id):
    print(user_id)
    profile = get_object_or_404(Profile, user_id=user_id)
    iban = profile.iban
    bank_name = profile.bank_name
    return JsonResponse({'iban': iban, 'bank_name': bank_name})




@login_required(login_url='login')
def end_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    for item in trip.items.all():
        if not item.is_paid:
            messages.error(request, 'You cannot end the trip with unpaid items!')
            return redirect('trip_details', trip_id=trip_id)

    if request.user not in trip.participants.all():
        messages.error(request, 'You are not a participant in this trip!')
        return redirect('home')
    
    if request.user == trip.leader:
        trip.has_ended = True
        trip.save()
    return redirect('trip_details', trip_id=trip_id)

@login_required(login_url='login')
def confirm_payment(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    if request.user not in trip.participants.all():
        messages.error(request, 'You are not a participant in this trip!')
        return redirect('home') 
    member = get_object_or_404(TripMember, trip=trip, member=request.user)
    if trip.has_ended:
        member.payment_confirmed = True
        member.save()
        messages.success(request, 'Payment confirmed!')
        return redirect('trip_details', trip_id=trip_id)
    
    messages.error(request, 'You cannot confirm payment for a trip that has not ended!')
    return redirect('trip_details', trip_id=trip_id)

def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    trip_id = item.trip.id
    item.delete()
    messages.success(request, 'Item deleted successfully!')
    return redirect('trip_details', trip_id=trip_id)


def set_profile(request):
    if request.method == 'POST':
        current_user = request.user
        iban = request.POST.get('iban')
        bank_name = request.POST.get('bank_name')
        profile = Profile.objects.get(user=current_user)
        profile.iban, profile.bank_name = iban, bank_name
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('home')
    return redirect('home')

