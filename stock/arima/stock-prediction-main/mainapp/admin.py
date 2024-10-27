from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path


class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        prediction = None
        if request.method == 'POST':
            symbol = request.POST.get('symbol')
            #prediction = Prediction.objects.filter(symbol=symbol).order_by('-created_at').first()
        
        context = {
            'site_title': self.site_title,
            'site_header': self.site_header,
            #'prediction': prediction,
        }
        return TemplateResponse(request, 'predict.html', context)  # Correctly referencing the template

# Instantiate the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')
