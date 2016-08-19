from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def overview(request):
    variables={}
    return render(request,'overview/index.html',variables)

def architecture(request):
    variables={}
    return render(request,'architecture/index.html',variables)

def tendency(request):
    variables={}
    return render(request,'tendency/index.html',variables)

def help(request):
    variables={}
    return render(request,'help/index.html',variables)

def test(request):
    variables={}
    return render(request,'test/index.html',variables)

def test2(request):
    variables={}
    return render(request,'test/index2.html',variables)
