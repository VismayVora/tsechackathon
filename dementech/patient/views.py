from django.shortcuts import render
from django.contrib.auth import authenticate,login

from rest_framework.authtoken.models import Token
from rest_framework import status,permissions,viewsets

from .models import *
from .serializers import *

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.decorators import action,api_view

from .whatsapp import send_message
from django.http import JsonResponse

import environ

env = environ.Env()
environ.Env.read_env()

# Create your views here.
class RegisterAPI(GenericAPIView):
	
	serializer_class = RegisterSerializer
	
	def post(self,request,*args,**kwargs):
		data = request.data
		serializer = self.serializer_class(data=data)
		serializer.is_valid(raise_exception = True)
		user = serializer.save()
		if not user.is_active:
			user.is_active = True
			user.save()
		token = Token.objects.create(user=user)
		
		return Response({'token' : token.key,'username' : user.username},status = status.HTTP_200_OK)

class LoginAPI(GenericAPIView):
	
	serializer_class = LoginSerializer
	
	def post(self,request,*args,**kwargs ):
		username = request.data.get('username',None)
		password = request.data.get('password',None)
		doc_code = request.data.get('doc_code',None)
		if password:
			user = authenticate(username = username, password = password)
		if doc_code:
			user = Patient.objects.get(doc_code=doc_code)
		if user :
			login(request,user)
			token = Token.objects.get(user=user)
			return Response({'token' : token.key,'username' : user.username},status = status.HTTP_200_OK)
		return Response('Invalid Credentials',status = status.HTTP_404_NOT_FOUND)

class MedicineAPI(viewsets.ModelViewSet):
	queryset = Medicine.objects.all()
	serializer_class = MedicineSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		medicine_objs = Medicine.objects.filter(patient = self.request.user)
		return medicine_objs
	
	def perform_create(self,serializer):
		serializer.save(patient = self.request.user)
	
	def update(self, request, *args, **kwargs):
		kwargs['partial'] = True
		return super().update(request, *args, **kwargs)

class ScrapBookAPI(viewsets.ModelViewSet):
	queryset = ScrapBook.objects.all()
	serializer_class = ScrapBookSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		scrap_objs = ScrapBook.objects.filter(patient = self.request.user)
		return scrap_objs
	
	def perform_create(self,serializer):
		serializer.save(patient = self.request.user)
	
	def update(self, request, *args, **kwargs):
		kwargs['partial'] = True
		return super().update(request, *args, **kwargs)

@api_view(['GET'])
def meetlink(self,request):
	patient = Patient.objects.get(user=self.request.user)
	gmeet_link = "https://meet.google.com/jsc-utht-fkj"
	message = f"Hello {patient.name}, a meeting has started. Click on this link to join the meeting: {gmeet_link}"
	send_message(request,message)

	return JsonResponse({"Message": "The message has been sent to the patient!"})
