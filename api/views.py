from django.shortcuts import render
from django.core.mail import EmailMessage
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.conf import settings
from knox.models import AuthToken
from .serializers import LoginUserSerializer, EmailSerializer
from .models import Newsletter
from .tasks import send_message
class ApiRoot(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)

    def list(self, request, format=None):
        return Response({
            'SendMailAPI': reverse('email', request=request, format=format),
            'Login': reverse('login', request=request, format=format),
            'Logout': reverse('knox_logout', request=request, format=format),
        })

#login API
class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token = AuthToken.objects.create(user)[1]
            return Response({
                "error": False,
                "message": "success",
                "user": LoginUserSerializer(user, context=self.get_serializer_context()).data,
                "token": token
            })
        else:
            return Response({
                "error": True,
                "message": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)




class SendMailAPI(generics.GenericAPIView):
    queryset = Newsletter.objects.all()
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = EmailSerializer
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            subject = request.data['subject']
            html_content = request.FILES['content'].read().decode('utf-8')
            recipients = request.data.getlist('recipients')
            email_count = len(recipients)
            send_message.delay(email_count, recipients, html_content, subject)
            return Response({
                "error":False,
                "message": "Success",
                "email_response": "emails added to queue successfully",
            }, status=status.HTTP_200_OK)    

            
        else:
            return Response({
                "error": True,
                "message": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    


            


