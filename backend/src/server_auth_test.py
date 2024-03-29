import pytest
import re
from subprocess import Popen, PIPE
import signal
from time import sleep
import requests
import json
from database import data
from other import clear
from error import InputError

# Use this fixture to get the URL of the server. It starts the server for you,
# so you don't need to.
@pytest.fixture
def url():
    url_re = re.compile(r' \* Running on ([^ ]*)')
    server = Popen(["python3", "src/server.py"], stderr=PIPE, stdout=PIPE)
    line = server.stderr.readline()
    local_url = url_re.match(line.decode())
    if local_url:
        yield local_url.group(1)
        # Terminate the server
        server.send_signal(signal.SIGINT)
        waited = 0
        while server.poll() is None and waited < 5:
            sleep(0.1)
            waited += 0.1
        if server.poll() is None:
            server.kill()
    else:
        server.kill()
        raise Exception("Couldn't get URL from local server")

def test_echo(url):
    '''
    A simple test to check echo
    '''
    resp = requests.get(url + 'echo', params={'data': 'hello'})
    assert json.loads(resp.text) == {'data': 'hello'}

def test_server_auth_register(url):
    # Normal register
    user0_data_input = {
        'email': "leonwu@gmail.com", 
        'password': "ihfeh3hgi00d", 
        'name_first': "Yilang",
        'name_last': "Wu",
    }
    r = requests.post(f"{url}/auth/register", json=user0_data_input)
    user0_data_output = r.json()
    assert user0_data_output['u_id'] == 0

    # Invalid email
    invalid_data_input1 = {
        'email': "ufhsdfkshfdhfsfhiw",
        'password': "uf89rgu",
        'name_first': "Andrew",
        'name_last': "Williams",
    }
    r = requests.post(f"{url}/auth/register", json=invalid_data_input1)
    invalid_data_output1 = r.json()
    assert invalid_data_output1['message'] == "<p>Email entered is not a valid email</p>"

    # Registered email register again
    invalid_data_input2 = {
        'email': "leonwu@gmail.com", 
        'password': "dfsdfskdfj", 
        'name_first': "haha",
        'name_last': "hehe",
    }
    r = requests.post(f"{url}/auth/register", json=invalid_data_input2)
    invalid_data_output2 = r.json()
    assert invalid_data_output2['message'] == '<p>Email address leonwu@gmail.com is already being used' \
        ' by another user</p>'

    # Password too short
    invalid_data_input3 = {
        'email': "hahaha@hehe.com", 
        'password': "dfsdf", 
        'name_first': "haha",
        'name_last': "hehe",
    }
    r = requests.post(f"{url}/auth/register", json=invalid_data_input3)
    invalid_data_output3 = r.json()
    assert invalid_data_output3['message'] == '<p>Password entered is less than 6 characters long</p>'

    # First Name too long
    invalid_data_input4 = {
        'email': "hahaha@hehe.com", 
        'password': "dfsddfdff", 
        'name_first': "h" * 51,
        'name_last': "hehe",
    }
    r = requests.post(f"{url}/auth/register", json=invalid_data_input4)
    invalid_data_output4 = r.json()
    assert invalid_data_output4['message'] == '<p>name_first is not between 1 and 50 characters inclusively' \
        ' in length</p>'

    # Last name too long
    invalid_data_input5 = {
        'email': "hahaha@hehe.com", 
        'password': "dfssdfdfdf", 
        'name_first': "haha",
        'name_last': "h" * 51,
    }
    r = requests.post(f"{url}/auth/register", json=invalid_data_input5)
    invalid_data_output5 = r.json()
    assert invalid_data_output5['message'] == '<p>name_last is not between 1 and 50 characters inclusively' \
        ' in length</p>'

def test_server_auth_logout(url):
    requests.delete(f"{url}/clear")

    # Register a user
    dataIn1 = {
        'email': "leonwu@gmail.com", 
        'password': "ihfeh3hgi00d", 
        'name_first': "Yilang",
        'name_last': "Wu",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn1)
    return_data1 = r.json()

    # Logout the user
    dataIn2 = {
        'token': return_data1['token']
    }
    r = requests.post(f"{url}/auth/logout", json=dataIn2)
    return_data2 = r.json()
    assert return_data2['is_success'] == True

    # Logout an invalid u_id
    dataIn3 = {
        'token': "fdfjskdfjwekjf"
    }
    r = requests.post(f"{url}/auth/logout", json=dataIn3)
    return_data3 = r.json()
    assert return_data3['message'] == "<p>Error, token is invalid</p>"

    # Logout a None token
    dataIn4 = {
        'token': None
    }
    r = requests.post(f"{url}/auth/logout", json=dataIn4)
    return_data4 = r.json()
    assert return_data4['is_success'] == False

def test_server_auth_login(url):
    requests.delete(f"{url}/clear")

    # Register a user
    dataIn1 = {
        'email': "leonwu@gmail.com", 
        'password': "ihfeh3hgi00d", 
        'name_first': "Yilang",
        'name_last': "Wu",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn1)
    return_data1 = r.json()

    # Log out this user
    dataIn2 = {
        'token': return_data1['token']
    }
    r = requests.post(f"{url}/auth/logout", json=dataIn2)

    # Log in this user with a wrong password
    dataIn3 = {
        'email': "leonwu@gmail.com",
        'password': "ihfeh3h",
    }
    r = requests.post(f"{url}/auth/login", json=dataIn3)
    return_data1 = r.json()
    assert return_data1['message'] == "<p>Password is not correct</p>"

    # Login with a invalid email
    dataIn4 = {
        'email': "dfksjfksjfkse",
        'password': "djfjskejfewsjf",
    }
    r = requests.post(f"{url}/auth/login", json=dataIn4)
    return_data2 = r.json()
    assert return_data2['message'] == "<p>Email entered is not a valid email</p>"

    # Login this user again
    dataIn5 = {
        'email': "leonwu@gmail.com",
        'password': "ihfeh3hgi00d",
    }
    r = requests.post(f"{url}/auth/login", json=dataIn5)
    return_data3 = r.json()
    assert return_data3['u_id'] == 0

    dataIn6 = {
        'email': "dfdskfj@fdf.com",
        'password': "sdfsdjkfsdfe"
    }
    r = requests.post(f"{url}/auth/login", json=dataIn6)
    return_data4 = r.json()
    assert return_data4['message'] == '<p>Error, email address dfdskfj@fdf.com has not been registered' \
        ' yet</p>'

def test_server_addowner(url):
    requests.delete(f"{url}/clear")
    # Register a user
    dataIn1 = {
        'email': "leonwu@gmail.com", 
        'password': "ihfeh3hgi00d", 
        'name_first': "Yilang",
        'name_last': "Wu",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn1)
    return_data1 = r.json()

    # Register another user
    dataIn2 = {
        'email': "billgates@outlook.com",
        'password': "VukkFs",
        'name_first': "Bill",
        'name_last': "Gates",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn2)
    return_data2 = r.json()

    # Channel created by the first user
    dataIn3 = {
        'token': return_data1['token'],
        'name': "group1",
        'is_public': True,
    }
    r = requests.post(f"{url}/channels/create", json=dataIn3)

    # The second user join the channel
    dataIn4 = {
        'token': return_data2['token'],
        'channel_id': 0,
    }
    r = requests.post(f"{url}/channel/join", json=dataIn4)
    
    # The first user add the second user as an owner to an invalid channel
    dataIn5 = {
        'token': return_data1['token'],
        'channel_id': 5,
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/addowner", json=dataIn5)
    return_data4 = r.json()
    assert return_data4['code'] == 400

    # The first user add him/herself as an owner, which is invalid
    dataIn6 = {
        'token': return_data1['token'],
        'channel_id': 0,
        'u_id': return_data1['u_id'],
    }
    r = requests.post(f"{url}/channel/addowner", json=dataIn6)
    return_data5 = r.json()
    assert return_data5['code'] == 400

    # Register the third user
    dataIn7 = {
        'email': "guanbin@gmail.com", 
        'password': "1234567890", 
        'name_first': "Guanbin",
        'name_last': "Wen",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn7)
    return_data6 = r.json()

    # The third user joined the channel    
    dataIn8 = {
        'token': return_data6['token'],
        'channel_id': 0,
    }
    r = requests.post(f"{url}/channel/join", json=dataIn8)

    # The second user add the third user as an owner, which is invalid
    dataIn9 = {
        'token': return_data2['token'],
        'channel_id': 0,
        'u_id': return_data6['u_id'],
    }
    r = requests.post(f"{url}/channel/addowner", json=dataIn9)
    return_data7 = r.json()
    assert return_data7['code'] == 400
    
    # The first user add the second user as an owner
    dataIn10 = {
        'token': return_data1['token'],
        'channel_id': 0,
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/addowner", json=dataIn10)

    # The first user obtain the channel details
    dataIn11 = {
        'token': return_data1['token'],
        'channel_id': 0,
    }
    r = requests.get(f"{url}/channel/details", params=dataIn11)
    return_data8 = r.json()
    is_owner = False
    for owner in return_data8['owner_members']:
        if return_data2['u_id'] == owner['u_id']:
            is_owner = True
    assert is_owner == True

def test_server_removeowner(url):
    requests.delete(f"{url}/clear")
    # Register a user
    dataIn1 = {
        'email': "leonwu@gmail.com", 
        'password': "ihfeh3hgi00d", 
        'name_first': "Yilang",
        'name_last': "Wu",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn1)
    return_data1 = r.json()

    # Register another user
    dataIn2 = {
        'email': "billgates@outlook.com",
        'password': "VukkFs",
        'name_first': "Bill",
        'name_last': "Gates",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn2)
    return_data2 = r.json()

    # Register the third user
    dataIn3 = {
        'email': "dennislin@outlook.com",
        'password': "tgbyhnUJM",
        'name_first': "Dennis",
        'name_last': "Lin",
    }
    r = requests.post(f"{url}/auth/register", json=dataIn3)
    return_data3 = r.json()

    # Channel created by the first user
    dataIn4 = {
        'token': return_data1['token'],
        'name': "The first",
        'is_public': True,
    }
    r = requests.post(f"{url}/channels/create", json=dataIn4)
    return_data4 = r.json()

    # The second user join the channel
    dataIn5 = {
        'token': return_data2['token'],
        'channel_id': 0,
    }
    r = requests.post(f"{url}/channel/join", json=dataIn5)

    # The first user add the second user as owner
    dataIn6 = {
        'token': return_data1['token'],
        'channel_id': return_data4['channel_id'],
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/addowner", json=dataIn6)

    # The first user remove the owner identity of the second user but input an invalid channel
    dataIn7 = {
        'token': return_data1['token'],
        'channel_id': 5,
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/removeowner", json=dataIn7)
    return_data5 = r.json()
    assert return_data5['code'] == 400

    # The first user wants to remove the third user out of owner but the third user is not an owner
    dataIn8 = {
        'token': return_data1['token'],
        'channel_id': return_data4['channel_id'],
        'u_id': return_data3['u_id'],
    }
    r = requests.post(f"{url}/channel/removeowner", json=dataIn8)
    return_data6 = r.json()
    assert return_data6['code'] == 400

    # The third user wants to remove the second user but the third is not an owner
    dataIn9 = {
        'token': return_data3['token'],
        'channel_id': return_data4['channel_id'],
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/removeowner", json=dataIn9)
    return_data7 = r.json()
    assert return_data7['code'] == 400

    # The first user remove the second user from owner
    dataIn10 = {
        'token': return_data1['token'],
        'channel_id': return_data4['channel_id'],
        'u_id': return_data2['u_id'],
    }
    r = requests.post(f"{url}/channel/removeowner", json=dataIn10)

    # The first user obtain the channel details
    dataIn11 = {
        'token': return_data1['token'],
        'channel_id': return_data4['channel_id'],
    }
    r = requests.get(f"{url}/channel/details", params=dataIn11)
    return_data8 = r.json()
    is_owner = False
    for owner in return_data8['owner_members']:
        if return_data2['u_id'] == owner['u_id']:
            is_owner = True
    assert is_owner == False

def test_server_password_reset_invalid0(url):
    '''invalid reset code provided by the owner of flockr'''
    clear()

    # Valid information has been summitted to register from the first user
    user0_data_input = {
        'email': "leonwu@gmail.com",
        'password': "ihfeh3hgi00d",
        'name_first': "Yilang",
        'name_last': "W"
    }
    r = requests.post(f"{url}/auth/register", json=user0_data_input)
    # Vadid information has been summitted to register from the second user
    user1_data_input = {
        'email': "billgates@outlook.com",
        'password': "VukkFs",
        'name_first': "Bill",
        'name_last': "Gates"
    }
    r = requests.post(f"{url}/auth/register", json=user1_data_input)
    # Vadid information has been summitted to register from the third user
    user2_data_input = {
        'email': "johnson@icloud.com",
        'password': "RFVtgb45678",
        'name_first': "M",
        'name_last': "Johnson"
    }
    r = requests.post(f"{url}/auth/register", json=user2_data_input)
    # User 0 send a password reset request
    user0_password_reset_request_input = {
        'email': "leonwu@gmail.com"
    }
    requests.post(f"{url}/auth/passwordreset/request", json=user0_password_reset_request_input)
    # User 0 change the password with invalid password
    user0_password_reset_input = {
        'reset_code': 1234,
        'new_password': "1q2w3w",
    }
    r = requests.post(f"{url}/auth/passwordreset/reset", \
        json=user0_password_reset_input)
    user0_reset_output = r.json()
    assert user0_reset_output['message'] == '<p>reset_code is not a valid reset code</p>'