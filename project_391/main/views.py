import random
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render, render_to_response
from main.models import Users, Persons, Session, Groups
from django.http import HttpResponse
from django.forms import EmailField
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
import logging
# Create your views here.

def loginPage(request):         # how do we respond to a request for a login page?

    if len(request.POST) == 0:  # "Sign In" not clicked, display log in page
        return render(request, 'main/login.html')

    # Otherwise, validate the login
    POST_username = request.POST.get('USERNAME', None)
    POST_password = request.POST.get('PASSWORD', None)
    error_msg = None

    if POST_username and POST_password:
        try:
            user = Users.objects.get(username=POST_username)
        except ObjectDoesNotExist:
            error_msg = "User %s does not exist." % username
        else:
            if user.password == POST_password:
                # Send them to the index page, and store a unique sessiontracker for this session.
                response = render_to_response('main/index.html',
                                              {'password':POST_password, 'username':POST_username},
                                              RequestContext(request))
                response.set_cookie('sessiontracker', str(hash(POST_username+str(random.random()))))
                # TODO store cookie in database
                return response
            else:
                error_msg = "Incorrect Password, please try again."
    else:
        error_msg = "Please supply a username and password."

    error_msg = error_msg if error_msg else "Unknown Error, please report"
    return render(request, 'main/login.html', {'error_msg' : error_msg})

################################################################################

def register(request):
    if len(request.POST) == 0:  # "Register" wasn't clicked; display the empty registration page
        return render(request, 'main/register.html')

    # Get form data
    firstname       = request.POST.get('FIRSTNAME', None)
    lastname        = request.POST.get('LASTNAME', None)
    username        = request.POST.get('USERNAME', None)
    address         = request.POST.get('ADDRESS', None)
    email           = request.POST.get('EMAIL', None)
    phone           = request.POST.get('PHONE', None)
    password        = request.POST.get('PASSWORD', None)
    passwordconfirm = request.POST.get('PASSWORDCONFIRM', None)

    ### Validation ###
    err_pass_not_match = False
    err_username_taken = False

    # Check whether username already exists
    try:
        Users.objects.get(username=username)
    except ObjectDoesNotExist: # good
        pass
    else:
        err_username_taken = True

    if phone:
        # Extract just the digits from the phone number
        phone = ''.join([char for char in phone if char.isdigit()])
        # Check whether length of number falls within valid international range
        if not 8 <= len(phone) <= 15: 
            phone = None

    # Check if supplied email is a valid email address
    try:
        email = EmailField().clean(email)
    except ValidationError:
        email = None

    # Check that passwords match if both given
    if password and passwordconfirm and password != passwordconfirm:
        err_pass_not_match = True
        
    # If any fields are None (meaning not POSTed or invalid), set its
    # error variable to True, else set to False.
    err_firstname = not firstname
    err_lastname = not lastname
    err_username = not username
    err_address = not address
    err_email = not email
    err_phone = not phone
    err_password = not password
    err_passwordconfirm = not passwordconfirm

    errors = {
        "err_firstname"       : err_firstname,
        "err_lastname"        : err_lastname,
        "err_username"        : err_username,
        "err_address"         : err_address,
        "err_email"           : err_email,
        "err_phone"           : err_phone,
        "err_password"        : err_password,
        "err_passwordconfirm" : err_passwordconfirm,
        "err_pass_not_match"  : err_pass_not_match,
        "err_username_taken"  : err_username_taken
    }
        
    if any(errors.values()):
        return render(request, 'main/register.html', errors)
    else:
        new_user = Users.objects.create(username=username,
                                        password=password)
        new_person = Persons.objects.create(user_name=new_user,
                                            first_name=firstname,
                                            last_name=lastname,
                                            address=address,
                                            email=email,
                                            phone=phone)

        assert new_person.user_name.password == password

        response = render_to_response('main/index.html',
                                      {'password':password, 'username':username},
                                      RequestContext(request))
        response.set_cookie('sessiontracker', str(hash(username+str(random.random()))))
        
        try:
            session = Session.objects.get(username__username=username)
        except ObjectDoesNotExist:
            Session.objects.create(username=new_user,
                                   sessiontracker=hash(username+str(random.random())))
        else:
            session.sessiontracker=hash(username+str(random.random()))
            session.save()

        return response
    
################################################################################

def temp_main_page(request):
    """
    Sandbox for Carl to test cookies/sessions. Beware: garbage lies below.
    """
    text = ""
    shash = int(request.COOKIES.get('sessiontracker', '0'))
    if shash == 1:
        text += 'session tracker is marked as expired (logged out)!'
    if shash == 0:
        text += 'no \'sessiontracker\' cookie exists.'
    else:
        text += 'session tracker cookie says %s<br/>'%shash
        try:
            user = Session.objects.get(sessiontracker=shash)
        except ObjectDoesNotExist:
            text += 'no session object with that id exists in database.\n'
        else:
            text += 'this corresponds to user %s'%user
        

    return render(request, 'main/index.html', {'temp_cookie_text':text})
            
################################################################################

def home_page(request):
    return render(request, 'main/home_page.html')
        
def upload(request):
    return render(request, 'main/uploads.html')
    
def photo_details(request):
    return render(request, 'main/photo_details.html')
    
def group_management(request):
    return render(request, 'main/group_management.html')

def remove_user_from_group(request):
    return render(request, 'main/group_management.html')

@csrf_exempt
def add_group(request):
    logger = logging.getLogger(__name__)
    # TODO Build an authenticate user function
    # user_name = authenticate_user(request)
    user_name = 'jonnyc'
    if request.POST:
        # receives a json object {"newGroupName":"nameOfNewGroup"}
        try:
            request_body = json.loads(request.body)
        except e:
            logger.error(e)
            return HttpResponse("Could not parse JSON add user request. \
                                new group requests should contain a request body \
                                formatted as {'newGroupName': 'nameOfNewGroup'}",
                                content_type="Apllication/json",
                                status=400)
        try:
            newGroupName = request_body["newGroupName"]
        except e:
            logger.error(e)
            return HttpResponse("Could not find property 'newGroupName' \
                                on the json request object. Ensure you pass a \
                                json object formatted like \
                                {'newGroupName': 'nameOfNewGroup'}",
                                status=400)
        
        # TODO set user_name to the users name based on session/cookie

        # Add the group to the Groups model
        user = Users.objects.get(username=user_name)
        try:
            new_group = Groups.objects.create(user_name=user, group_name=newGroupName)
        except IntegrityError as e:
            logger.error(e)
            return HttpResponse("A Group by this name already exists", status=400)

        # Ensure group was added
        try:
            assert isinstance(Groups.objects.get(user_name=user_name, group_name=newGroupName), Groups)
        except AssertionError as e:
            logger.error(e)
            return HttpResponse("Valid request but server errored when adding group" + "\n" + e,
                                status=500)

        # Return success response
        return HttpResponse("Groups succesfully added to server: " + request.body.decode("utf-8"),
                                status=200)
    else:
        return HttpResponse("Only POST requests can be used to add groups",
                                status=400)
    
def add_user_to_group(request):
    return




def authenticat_user(request):
    # if user can't be authenticated
    # if authenticated 
    # return username string
    return HttpResponse("Could not authenticate")
