from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate_queryset(request, queryset, per_page=10):
    """
    Helper function to paginate a queryset
    """
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        items = paginator.page(paginator.num_pages)
    
    return items
