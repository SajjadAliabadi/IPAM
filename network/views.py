from django.shortcuts import render

# Create your views here.


from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if not username or not password:
            messages.error(request, "Username and Password are required.")
            return redirect('register')
            
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')
            
        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        user.is_staff = True # Essential for them to log into the admin panel!
        user.save()
        
        requester_group, _ = Group.objects.get_or_create(name='Requester')
        user.groups.add(requester_group)
        
        messages.success(request, "Registration successful! You can now log in.")
        return redirect('admin:login')
        
    return render(request, 'admin/register.html')
