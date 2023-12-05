
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

# Connect to the database
from miksisdk.base import DatabaseConnector

# Database Credentials
db_password = os.getenv("password")
print("Hosted password", db_password)
db_user = os.getenv("db_user")
db_host = os.getenv("db_host")
db_name = os.getenv("database_name")



def get_db():
    connector = DatabaseConnector(db_user=db_user, db_password=db_password,
                                  db_host=db_host, db_name=db_name)
    db = connector.getdbinstance()
    return db


def get_connection_status():
    connector = DatabaseConnector(db_user=db_user, db_password=db_password,
                                  db_host=db_host, db_name=db_name)
    status = connector.connect()
    return status


def check_database_connection_status():
    status = get_connection_status()
    return status

@csrf_exempt
def check_database_connection_status(request):
    # Check if user is logged in via session
    user_id = request.session.get('user_id')
    if not user_id:
        # Return a JSON response indicating the user is not logged in
        return JsonResponse({'error': 'User not logged in'}, status=401)

    try:
        # Check database connection status
        status = get_connection_status()
    except Exception as e:
        # Handle exceptions and return an error in JSON format
        return JsonResponse({'error': 'Database connection error', 'details': str(e)}, status=500)

    # Return a JSON response with the status of the database connection
    return JsonResponse({'status': 'connected' if status else 'not connected'})


miksi_api_key = os.getenv("miksi_api_key")




from miksisdk.api import MiksiAPIHandler
from miksisdk.agent import AgentInitializer

def create_agent():
    try:
        db = get_db()
        print("db", db)
        if db is None:
            raise ValueError("Database connection failed")

        model = MiksiAPIHandler(miksi_api_key=miksi_api_key)
        print("model: ", model)
        if model is None:
            raise ValueError("MiksiAPIHandler initialization failed")

        llm = model.get_default_llm(miksi_api_key=miksi_api_key)
        print("llm: ", llm)
        if llm is None:
            raise ValueError("Getting default LLM failed")

        path = '/home/miksi/Miksi-SDK-in-Production/media/images'

        agent_initializer = AgentInitializer(llm, db, miksi_api_key=miksi_api_key, path = path)
        print("agent_initializer: ", agent_initializer)
        agent = agent_initializer.create_agent()
        print('agent: ', agent)
        if agent is None:
            raise ValueError("Agent creation failed")

    except Exception as e:
        print("exception: ", e)
        # Return a JSON response with the error details
        return JsonResponse({'error': 'Error during agent creation process', 'details': str(e)}, status=500)

    # If everything went well, return a success response
    return agent

from django.conf import settings

images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
print("The images are in: ", images_dir)

@csrf_exempt
def process_request(request):
    # Check if user is logged in via session
    # ... your login check logic ...

    # Check if query is provided
    query = request.POST.get("query")
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    # Use the MEDIA_ROOT from settings to get the initial state of the directory
    images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
    print("The images are in: ", images_dir)
    initial_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                     for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

    try:
        # Create an agent and run it with the query
        # ... your agent creation and execution logic ...
        agent = create_agent()  # Assuming create_agent() is defined elsewhere
        response = agent.run(query)
    except Exception as e:
        # Handle any errors during agent creation or execution
        return JsonResponse({'error': 'Error processing request', 'details': str(e)}, status=500)

    # Check the directory after execution using MEDIA_ROOT
    final_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                   for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

    # Detect new or modified files
    new_or_modified_files = [f for f in final_files if f not in initial_files or final_files[f] != initial_files.get(f)]

    # Prepare the response
    response_data = {'response': response}

    # If there's a new or modified file, add its path to the response
    if new_or_modified_files:
        new_file = new_or_modified_files[0]  # First new or modified file
        image_url = os.path.join(settings.MEDIA_URL, 'images', new_file)
        response_data['image'] = request.build_absolute_uri(image_url)

    return JsonResponse(response_data)

'''
@csrf_exempt
def process_request(request):
    # Check if user is logged in via session

    # Check if query is provided
    query = request.POST.get("query")
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    # Get the initial state of the directory
    images_dir = os.path.join(settings.BASE_DIR, 'media/images')
    initial_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                     for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

    try:
        # Create an agent and run it with the query
        print("before agent status")
        agent = create_agent()
        print("agent created")
        response = agent.run(query)
        print("response obtained")
    except Exception as e:
        # Handle any errors during agent creation or execution
        return JsonResponse({'error': 'Error processing request', 'details': str(e)}, status=500)

    # Check the directory after execution
    final_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                   for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

    # Detect new or modified files
    new_or_modified_files = [f for f in final_files if f not in initial_files or final_files[f] != initial_files.get(f)]

    # Prepare the response
    response_data = {'response': response}

    # If there's a new or modified file, add its path to the response
    if new_or_modified_files:
        new_file = new_or_modified_files[0]  # First new or modified file
        image_url = settings.MEDIA_URL + 'images/' + new_file
        response_data['image'] = request.build_absolute_uri(image_url)

    return JsonResponse(response_data)
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