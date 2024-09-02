from rest_framework.decorators import api_view


@api_view(["POST"])
def postcall_webhook(request):
    # request.POST.get()
    pass