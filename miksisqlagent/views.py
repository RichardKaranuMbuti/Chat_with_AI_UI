
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
from miksisdk.base import MySQLDatabaseConnector

# Load Database Credentials
db_password = os.getenv("db_password")
db_user = os.getenv("db_user")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")
print(db_name)

#Establish connection to the db
def connect():
     connector = MySQLDatabaseConnector(db_user=db_user, db_password=db_password,
                                        db_host=db_host, db_name=db_name)
     status = connector.connect()
     return status

status = connect()
print (status)
print("This is the checkpoint>>>>.........HERE ")
print(db_name)
miksi_api_key = os.getenv("miksi_api_key")
print(miksi_api_key)

#Get an instabce of the db
def get_db():
     connector = MySQLDatabaseConnector(db_user=db_user, db_password=db_password,
                                         db_host=db_host, db_name=db_name)
     db = connector.getdbinstance()
     return db

db = get_db()

# Check if api key is valid
from miksisdk.api import MiksiAPIHandler
from llama_index.llms import AzureOpenAI
import os

miksi_api_response = MiksiAPIHandler(miksi_api_key=miksi_api_key)
miksi_api_key_status = miksi_api_response.validate_miksi_api_key()
print(f"Key status: {miksi_api_key_status}")

os.environ["OPENAI_API_KEY"] = os.getenv("openai_api_key")
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://miksi.openai.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"

azure_llm = AzureOpenAI( engine="miksisdk", model="gpt-35-turbo-16k", temperature=0.0,
                   azure_endpoint="https://miksi.openai.azure.com/",
                    api_key=os.getenv("azure_openai_key"),
                    api_version="2023-07-01-preview", )


from miksisdk.agent import CreateChatAgent
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# The function to processs query using llama_agent
@csrf_exempt
@require_http_methods(["POST"])
def query_api(request):
    # Check if the query exists and is not empty
    query = request.POST.get('query', '')
    llm = azure_llm
    if not query:
        return JsonResponse({'error': 'Query is required and cannot be empty'}, status=400)

    try:
        # Attempt to connect to the database and create the agent
        db = get_db()
        if db is None:
            raise ValueError("Database connection failed")

        # Initialize the agent and query engine
        agent = CreateChatAgent(db=db, miksi_api_key=miksi_api_key)
        query_engine = agent.create_query_engine()

        # Execute the query
        response = query_engine.query(query)

        # Extracting information from the response
        main_response = response.response
        sql_query = response.metadata['sql_query']

        # Return the structured response and SQL query in JSON format
        return JsonResponse({
            'main_response': main_response,
            'sql_query': sql_query,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from miksisdk.graphtool import MySQLDatabaseGraphTool
from miksisdk.agent import CreateGraphAgent, run_agent
from pandasai.llm import OpenAI
import logging

try:
     db_tool = MySQLDatabaseGraphTool(username=db_user, password=db_password,
                                      host=db_host, database=db_name)
     print(f"db_tool: {db_tool} ")
     db_tool.connect()
     dfs = db_tool.prepare_data()
     db_tool.print_table_schemas()
except Exception as e: logging.error(f"An error occurred: {e}")

user_defined_path='media/images'
pandas_llm = OpenAI(api_token=os.getenv("openai_api_key"))

agent_instance = CreateGraphAgent(miksi_api_key=miksi_api_key, prepared_data= dfs,
                                   llm= pandas_llm, user_defined_path=user_defined_path)

agent = agent_instance.create_graph_engine()

def run_graph_agent(query):
    response = run_agent(agent,question=query)
    return response

DJANGO_ENV = os.getenv('DJANGO_ENV')


from django.conf import settings

@csrf_exempt
def run_graph_agent(request):
    query = request.POST.get('query', '')
    if not query:
        return JsonResponse({'error': 'Query is required and cannot be empty'}, status=400)
    try:
        # Use the MEDIA_ROOT from settings to get the initial state of the directory
        images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
        print("The images are in: ", images_dir)
        initial_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                         for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

        # Run the agent, which might create or modify files
        response = run_agent(agent, question=query)

        # Check the directory after execution
        final_files = {f: os.path.getmtime(os.path.join(images_dir, f))
                       for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))}

        # Detect new or modified files
        new_or_modified_files = [f for f in final_files if f not in initial_files or final_files[f] != initial_files.get(f)]

        # Prepare the response data
        response_data = {'response': response}

        # If there's a new or modified file, add its path to the response
        if new_or_modified_files:
            new_file = new_or_modified_files[0]  # Assuming we only care about the first new or modified file
            image_url = os.path.join(settings.MEDIA_URL, 'images', new_file)
            response_data['image'] = request.build_absolute_uri(image_url)

        return JsonResponse(response_data)

    except Exception as e:
        # Handle any potential errors gracefully
        return JsonResponse({'error': str(e)}, status=500)


# Render templates
def render_signup(request):
    return render(request, 'miksisqlagent/signup.html')

def render_home(request):
    return render(request, 'miksisqlagent/base.html')


def show_login_template(request):
    return render(request, 'miksisqlagent/login.html')

def chat_page(request):
    return render( request, 'miksisqlagent/chat.html')