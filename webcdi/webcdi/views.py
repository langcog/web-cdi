from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

from webcdi.forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.researcher.institution = form.cleaned_data.get('institution')
            user.researcher.position = form.cleaned_data.get('position')
            user.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('console')
    else:
        form = SignUpForm()
    return render(request, 'webcdi/signup.html', {'form': form})