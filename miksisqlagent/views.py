
from django.shortcuts import render
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from .models import UserSignup
from django.http import HttpResponse
import os
from django.http import HttpResponseServerError
from django.conf import settings
import json
from django.core.exceptions import ObjectDoesNotExist
import uuid
from django.contrib.auth.hashers import check_password

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import UserSignup
from django.urls import reverse
from dotenv import load_dotenv

load_dotenv()

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        # Retrieve the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email').lower()  # Convert email to lowercase
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if password and confirm_password match
        if password != confirm_password:
            return JsonResponse({
                'message': 'Passwords do not match',
                'status': 400  # 400 Bad Request
            })

        try:
            # Check if a user with the provided email already exists
            if UserSignup.objects.filter(email=email).exists():
                raise ValueError("The email provided is already in use")

            # Hash the password before storing it
            hashed_password = make_password(password)

            # Create a new UserSignup object and save
            user_signup = UserSignup(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hashed_password
            )
            user_signup.save()

            # If all operations were successful, return a positive response
            return JsonResponse({
                'message': 'Signup successful',
                'status': 200  # 200 OK

            })

        except ValueError as e:
            return JsonResponse({
                'message': str(e),
                'status': 409  # 409 Conflict for duplicate email

            })
        except Exception as e:
            # This block will catch other exceptions that might occur
            return JsonResponse({
                'message': 'An error occurred during signup. Please try again.',
                "error": e ,
                'status': 500  # 500 Internal Server Error
            })


# Log in the User

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        print("password: ", password)

        try:
            user = UserSignup.objects.get(email=email)
            print("user : ", user)
        except UserSignup.DoesNotExist:
            return JsonResponse({'message': 'User not found.Check your login details'}, status=401)

        if check_password(password, user.password):
            request.session['user_id'] = user.user_id  # Store user_id in session
            stored_user_id = request.session.get('user_id')
            authenticated = True
            print("Stored user_id: ", stored_user_id)

            return JsonResponse({'user_id': user.user_id,'status': 200})
        if authenticated:
            next_page = request.POST.get('next') or '/'
            return redirect(next_page)
        else:
            return JsonResponse({'message': 'Check your login details'}, status=401)

    next_page = request.GET.get('next') or '/'
    context = {'next': next_page}
    return render(request, 'login.html', context)

    return JsonResponse({'message': 'Invalid request'}, status=400)




# Load Database Credentials
db_password = os.getenv("db_password")
db_user = os.getenv("db_user")
db_host = 'localhost'
print(f"db host: {db_host}")
db_name = os.getenv("db_name")
print(f"db name: {db_name}")
db_port = 3306
engine = 'MySQL'



miksi_api_key = os.getenv('miksi_api_key')
print(miksi_api_key)


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from miksiai.utils import check_connection, set_db

media_path = 'media/images'

@csrf_exempt
def set_db_and_check_connection(request):
    if request.method == 'POST':    
        if not all([db_name, db_user, db_password, db_host, db_port]):
            return JsonResponse({"error": "All database credentials must be provided."}, status=400)
        try:
            set_db(db_name, db_user, db_password, db_host, db_port)
            status = check_connection(engine=engine)
            return JsonResponse({"status": status})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)
    

from miksiai.master import initialize_env

env_path = 'venvs'


@csrf_exempt
def initialize_env_view(request):
    if request.method == 'POST':
        try:
            initialize_env(env_path)
            return JsonResponse({"message": "Environment initialized successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)

from miksiai.agent import create_agent, run_agent

@csrf_exempt
def process_questions(request):
    if request.method == 'POST':
        instructions = request.POST.get('instructions', '')
        query = request.POST.get('query')
        print("Received request with instructions and query")

        if not query:
            return JsonResponse({"error": "Query cannot be empty."}, status=400)
        
        if not all([db_name, db_user, db_password, db_host, db_port]):
            return JsonResponse({"error": "All database credentials must be provided."}, status=400)
        
        try:
            print("Attempting to create agent")
            agent = create_agent(miksi_api_key=miksi_api_key,
                                 engine=engine,
                                 db_name=db_name, db_user=db_user, db_password=db_password,
                                 db_host=db_host, db_port=db_port, instructions=instructions)
            print(f"Agent created: {agent}")
            
            # Use the MEDIA_ROOT from settings to get the initial state of the directory
            images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
            print("The images are in:", images_dir)
            initial_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                             for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}
            
            # Run the agent, which might create or modify files
            response = run_agent(agent, miksi_api_key, query, media_path)
            print(f"final answer: {response}")

            # At this point, response is already a dictionary
            if not isinstance(response, dict):
                return JsonResponse({"error": "Invalid response from agent"}, status=500)

            response_dict = response

            # Check the directory after execution
            final_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                           for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}
            
            # Detect new or modified files
            new_or_modified_files = [f for f in final_files if f not in initial_files or final_files[f] != initial_files[f]]
            
            # If there are new or modified files, add their paths to the response
            if new_or_modified_files:
                image_urls = [request.build_absolute_uri(os.path.join(settings.MEDIA_URL, 'images', f)) for f in new_or_modified_files]
                response_dict['image_path'] = image_urls
            
            return JsonResponse(response_dict)
        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)
    
    
    
DJANGO_ENV = os.getenv('DJANGO_ENV')


from django.conf import settings
import re

def remove_json_formatters(text):
    # Define the pattern to match ```json at the beginning and ``` at the end.
    pattern = r'```json|```'
    
    # Replace occurrences of the pattern with an empty string.
    cleaned_text = re.sub(pattern, '', text)
    
    return cleaned_text

'''
@csrf_exempt
def process_questions(request):
    query = request.POST.get('query', '')
    if not query:
        return JsonResponse({'error': 'No question to process.'}, status=400)
    try:
        # Use the MEDIA_ROOT from settings to get the initial state of the directory
        images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
        print("The images are in: ", images_dir)
        initial_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                         for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}
        
        # Run the agent, which might create or modify files
        response = remove_json_formatters(run_agent(agent, miksi_api_key, query))
        print(f"final answer: {response}")

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            # Handle the error if response is not a valid JSON string
            response_dict = {}
        
        # Check the directory after execution
        final_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                       for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}
        
        # Detect new or modified files
        new_or_modified_files = [f for f in final_files if f not in initial_files or final_files[f] != initial_files[f]]
        
        # Prepare the response data
        response_data = {'response': response_dict}
        
        # If there are new or modified files, add their paths to the response
        if new_or_modified_files:
            image_urls = [request.build_absolute_uri(os.path.join(settings.MEDIA_URL, 'images', f)) for f in new_or_modified_files]
            response_data['images'] = image_urls
        
        return JsonResponse(response_data)
    
    except Exception as e:
        # Handle any potential errors gracefully
        return JsonResponse({'error': str(e)}, status=500)

'''
# Render templates
def render_signup(request):
    return render(request, 'miksisqlagent/signup.html')

def render_home(request):
    return render(request, 'miksisqlagent/base.html')


def show_login_template(request):
    return render(request, 'miksisqlagent/login.html')

def chat_page(request):
    return render( request, 'miksisqlagent/chat.html')

def setup_page(request):
    return render( request, 'miksisqlagent/setup.html')