from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import mysql.connector
from django.contrib import messages
from decouple import config
from google.genai import Client
from django.http import JsonResponse
from django.conf import settings
import os,json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path
from langchain_mistralai import MistralAIEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from django.contrib.auth import logout,authenticate,login
from django.contrib.auth.decorators import login_required
from .forms import FileUploadForm
def firstpage(request):
    return render(request, "firstpage.html")

def setting(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        birth_date = request.POST.get('dob')
        gender = request.POST.get('gender')
        profile_image = request.FILES.get('profile_image')

        # 👇 Print to terminal
        print("Username:", username)
        print("Birth date:", birth_date)
        print("Gender:", gender)
        if profile_image:
            print(profile_image.name)

            image_filename = profile_image.name
            save_path = os.path.join(settings.MEDIA_ROOT, 'profile_pic')
            os.makedirs(save_path, exist_ok=True)

            image_path=os.path.join(save_path,image_filename)
            with open(image_path, 'wb+') as destination:
                for chunk in profile_image.chunks():
                    destination.write(chunk)

            print("Image saved to:", save_path)
            
        print("Profile image:", profile_image.name)
        profile_pic=profile_image.name
        user_email = request.COOKIES.get('user_email')
        print(user_email)
        # Connect to MySQL database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="wtl_project",
        )
        mycur=mydb.cursor() 
        myquery="UPDATE usermast SET uname=%s, birthdate=%s , gender=%s,profile_pic=%s WHERE uemail=%s"
        print(myquery)
        mycur.execute(myquery,[username,birth_date,gender,profile_pic,user_email])
        print(mycur)
        mydb.commit()
        mycur.close()
        mydb.close()
        # return HttpResponse("Form submitted successfully!")
    return render(request, "setting.html")

def home(request):
    user_email = request.COOKIES.get('user_email', None)  # Retrieve cookie
    is_logged_in = user_email is not None
    profile_picture=None

    # if user_email:
    #     mydb = mysql.connector.connect(
    #         host="localhost",
    #         user="root",
    #         password="",
    #         database="wtl_project",
    #     )
    #         mycur=mydb.cursor()
    #         mycur.execute("select profile_pic from usermast where uemail='"+user_email+"';")
    #         print(mycur)
    #         mydata=mycur.fetchone()
    #         print(mydata)
    #         if mydata:
    #             profile_picture=mydata[0]
    #     except Exception as e:
    #         print(f"Database error: {e}")
    #     finally:
    #         mycur.close()
    #         mydb.close()
    return render(request, 'home.html', {
        'is_logged_in': is_logged_in,
        'user_email': user_email
        # 'profile_image_url':profile_picture
    })
    return render(request, 'home.html')

def chattoai(request):
    api_key=config('CHAT_TO_AI')
    # print(api_key)
    client = Client(api_key=api_key)
    system_prompt = """
        Your an AI assistant whose work on the simple message of user.
        and you give the user friendly message.
        And the also 
    """
    if request.method == "POST":
        user_input = request.POST.get("message", "")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                system_prompt,
                user_input
            ],
        )
        return JsonResponse({"response": response.text})
    return render(request, "chattoai.html")

@csrf_exempt
def aboutinfo(request):
    if request.method == 'POST':
        try:
            raw_body=request.body.decode('utf-8')
            print("Raw request body:", raw_body) # Debugging
            data = json.loads(raw_body)
            responses = data.get('responses', '')
            print("Received responses:", responses)
            
            response_dict = {}
            for line in responses.splitlines():
                key, value = line.split(':', 1)  # Split into key and value
                response_dict[key.strip()] = value.strip()

                    # Access individual values
            name = response_dict.get('name')
            age = response_dict.get('age')
            gender = response_dict.get('gender')
            like = response_dict.get('likes')
            nature = response_dict.get('nature')
            # global system_prompt_for_own
            system_prompt_for_own = f"""
                You are an AI Assistant of {name}.
                Your age is {age}. You always talk like your age number.
                Your gender is {gender} version, So talk based on your gender.
                and your hobbies are {like}.
                and your mood is always a {nature} . Always talk in your moode. 
                Use a some time emojis for chatting in a one chat 1 or 2 emojis only.
                And the give the proper answer based on the provided contain.
            """
            request.session['system_prompt_for_own'] = system_prompt_for_own
            # global system_prompt_for_own = system_prompt1
            print("System Prompt:", system_prompt_for_own)
        except json.JSONDecodeError as e:
                print("JSON Decode Error:", e)
                return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return render(request, 'aboutinfo.html')

@csrf_exempt
def builtownai(request):
    system_prompt_for_own=request.session.get('system_prompt_for_own', None)
    # print("this is ",system_prompt_for_own)
    system_prompt=system_prompt_for_own
    if request.method == 'POST':
        api_key=config('BUILT_OWN_AI')
        # print(api_key)
        client = Client(api_key=api_key)
        user_input =request.POST.get("message", "")
        print(user_input)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
               contents=[
                    system_prompt,
                    user_input
                ],
            )
        # print("AI Response:", response.text)
        return JsonResponse({"response": response.text})
    return render(request, "builtownai.html")

vector_store=None
@csrf_exempt 
def chattopdf(request):
    global vector_store
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            
            # Save the file to the media folder
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
           
            file_name=file.name
            print(file_name)
            try:
                media_path = Path(settings.MEDIA_ROOT)
                pdf_path= media_path / file_name;
                print(pdf_path)

                #Load and process PDF
                loader=PyPDFLoader(file_path=pdf_path)
                docs=loader.load()
                print(docs[0])
                text_spiltter=RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                )

                split_docs=text_spiltter.split_documents(documents=docs)
                print(split_docs[0])
                api_key =config("MISTRAL_API_KEY") 
                model = "mistral-embed"
                embedder = MistralAIEmbeddings(
                    model=model,
                    api_key=api_key
                )
                # print(embedder)
                vector_store=QdrantVectorStore.from_documents(
                    collection_name="talk_to_pdf",
                    url="http://localhost:6333",
                    embedding=embedder,
                    documents=split_docs,
                )
                # print(vector_store[0])
                return JsonResponse({'message': f'File "{file.name}" uploaded and processed successfully!'}, status=200)
            except Exception as e:
                return JsonResponse({'error': f'Error processing PDF: {str(e)}'}, status=500)
        # handle querying

        elif 'application/json' in request.content_type:
            data=json.loads(request.body)
            message=data.get('message')
            if not message:
                    return JsonResponse({'error': 'No message provided'}, status=400)

            if not vector_store:
                return JsonResponse({'error': 'No PDF uploaded or processed yet.'}, status=400)
            
            
            search_result=vector_store.similarity_search(query=message)
            retrieved_text = "\n".join([result.page_content for result in search_result])
            api_key=config('CHAT_TO_AI')
            client = Client(api_key=api_key)
            system_prompt = f"""
                Your an AI assistant whose work on the find the answer based on the relevant chunk.
                You give the user friendly message.
                The answer you give the minumum but the add the proper words that fulfill the answer 
                the user ask about the related question.
                And the also the answer give to the {search_result}.
                Based on this text: {retrieved_text}, answer the user's query: {message}
            """
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                    contents=[
                        system_prompt,
                            message
                        ],
                )
            print(f"AI response: {response.text}")
            return JsonResponse({'response': response.text}, status=200)
    return render(request, 'upload.html', {'success': "Upload a PDF and ask questions!"})
    
@csrf_exempt
def sign_in(request):
    if request.method == 'POST':
        useremail = request.POST.get('signin-email')
        passw = request.POST.get('signin-password')

        print("Email:", useremail, "Password:", passw)
        try:
            # Connect to MySQL database
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="wtl_project",
            )
            mycur=mydb.cursor()
            mycur.execute("select * from usermast where uemail='"+useremail+"' and upass='"+passw+"' ;")
            print(mycur)
            mydata=mycur.fetchone()
            print(mydata)
            
            if mydata is not None:
                print("email and password is correct")
                response= redirect('/home/')
                response.set_cookie('user_email',useremail)
                return response
                # return render(request, 'home.html',{"email":useremail})
                # return render(request, 'home.html')
            else:
                return render(request, 'signin.html', {'error': 'Invalid credentials'})
        except mysql.connector.Error as err:
            return render(request, 'signin.html', {'error': f"Database error: {err}"})
        finally:
            if mydb.is_connected():
                mycur.close()
                mydb.close()
    return render(request, 'signin.html')

def signup(request):
    # try :
    #     s1=request.POST.get("signup-name")
    #     s2=request.POST.get("signup-email")
    #     s3=request.POST.get("signup-password")
    #     s4=request.POST.get("signup-repassword")


    #     name=str(s1)
    #     email=str(s2)
    #     password=str(s3)
    #     mydb=mysql.connector.connect(
    #         host="localhost",
    #         user="root",
    #         password="",
    #         database="wtl_project",
    #     )

    #     mycur=mydb.cursor()
    #     mycur.execute("INSERT INTO usermast(uname, uemail, upass) VALUES ('"+name+"','"+email+"','"+password+"');")
    #     mydb.commit()
    #     return render(request, 'home.html')
    
    # except mysql.connector.Error as err:
    #    return HttpResponse("hellllll"+err)
    if request.method == "POST":
        name = request.POST.get("signup-name")
        email = request.POST.get("signup-email")
        password = request.POST.get("signup-password")
        repassword = request.POST.get("signup-repassword")

        if password != repassword:
            return HttpResponse("<h1>Passwords do not match.</h1>")

        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="wtl_project",
            )
            mycur = mydb.cursor()

            # ✅ Secure way to insert data (prevents SQL injection)
            mycur.execute(
                "INSERT INTO usermast(uname, uemail, upass) VALUES (%s, %s, %s)",
                (name, email, password)
            )
            mydb.commit()
            mycur.close()
            mydb.close()
            messages.success(request, "Sign-up successsful. Please sign in.")
            return redirect('signin')  # Redirect to signin after success
        except mysql.connector.Error as err:
            return HttpResponse(f"<h1>Database Error: {err}</h1>")

    return render(request, 'signup.html')

def aboutus(request):
    return render(request, 'aboutus.html')

def custom_logout(request):
    response = redirect('/signin/')
    response.delete_cookie('user_email')  # Clear cookie
    return response
    # logout(request)
    # return redirect('signin')