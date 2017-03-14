from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import Awards, Institutions, Organizations, Investigators
from django.urls import reverse


# Create your views here.

def index(request):
    count = 0
    results = Awards.objects.all()
    try:
        amt = int(request.POST['amount'])
        count += 1

    except:
        pass

    else:
        results = results.filter(amount__gt=0.9*amt, amount__lt=1.1*amt)

    try:
        start = request.POST['start']
        end = request.POST['end']
        start_val = int(start[3:] + start[:2])
        end_val = int(end[3:] + end[:2])
        count += 1 

    except:
        pass
    
    else:
        results = results.raw('select * from awards where cast(substr(start_date, 7,10) || substr(start_date,\
         1,2) as integer) between %s and %s', [start_val, end_val])


    num = 2
    total = 0
    # if count > 0:
    #     num = len(results)
    if num > 0:
        for i in results:
            total +=i.amount
        return render(request,'plot/search_results.html', {'num':num, 'total':total, \
            'results':results})

    return render(request, 'plot/index.html', {})


def search_results(request, num, results):
    pass

def abstract(request):
    HttpResponse('Abstract')

