# api/tests/test_auth.py

import unittest

from auth import db
from auth.db_access.models import User, BlacklistToken
from auth.tests.base import BaseTestCase

import json
import time

def register_user(self, username, email, password):
    return self.client.post(
        '/auth/register',
        data=json.dumps(dict(
            email=email,
            password=password,
            username=username
        )),
        content_type='application/json',
    )

def login_user(self, email, password):
    return self.client.post(
        '/auth/login',
        data=json.dumps(dict(
            email=email,
            password=password,
        )),
        content_type='application/json',
    )

class TestAuthBlueprint(BaseTestCase):

  def test_registration(self):
    """ Test for user registration """

    with self.client:
        response = register_user(self,'yuanti', 'yuanti@gmail.com', 'freewifi')
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'success')
        self.assertTrue(data['message'] == 'Successfully registered.')
        self.assertTrue(data['access_token'])
        self.assertTrue(data['refresh_token'])
        self.assertTrue(response.content_type == 'application/json')
        self.assertEqual(response.status_code, 201)

  def test_registered_with_already_registered_email(self):
    """ Test registration with already registered email"""
    user = User(
        email='yuanti@gmail.com',
        password='freewifi',
        username='yuanti'
    )
    db.session.add(user)
    db.session.commit()
    with self.client:
        response = register_user(self,'yuanti', 'yuanti@gmail.com', 'freewifi')
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'fail')
        self.assertTrue(response.content_type == 'application/json')
        self.assertEqual(response.status_code, 202)

  def test_registered_with_already_registered_username(self):
    """ Test registration with already registered user"""
    user = User(
        email='yuanti2@gmail.com',
        password='freewifi',
        username='yuanti'
    )
    db.session.add(user)
    db.session.commit()
    with self.client:
        response = register_user(self,'yuanti', 'yuanti@gmail.com', 'freewifi')
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'fail')
        self.assertTrue(response.content_type == 'application/json')
        self.assertEqual(response.status_code, 202)

  def test_registered_user_login(self):
    """ Test for login of registered-user login """
    with self.client:
        # user registration
        resp_register = register_user(self, 'yuanti', 'yuanti@gmail.com', 'freewifi')
        data_register = json.loads(resp_register.data.decode())
        self.assertTrue(data_register['status'] == 'success')
        self.assertTrue(data_register['access_token'])
        self.assertTrue(data_register['refresh_token'])
        self.assertTrue(resp_register.content_type == 'application/json')
        self.assertEqual(resp_register.status_code, 201)
        # registered user login
        response = self.client.post(
            '/auth/login',
            data=json.dumps(dict(
                username='yuanti',
                email='yuanti@gmail.com',
                password='freewifi'
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'success')
        self.assertTrue(data['message'] == 'Successfully logged in.')
        self.assertTrue(data['refresh_token'])
        self.assertTrue(data['access_token'])
        self.assertTrue(response.content_type == 'application/json')
        self.assertEqual(response.status_code, 200)

  def test_non_registered_user_login(self):
    """ Test for login of non-registered user """
    with self.client:
        response = self.client.post(
            '/auth/login',
            data=json.dumps(dict(
                email='joe@gmail.com',
                password='123456'
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'fail')
        self.assertTrue(data['message'] == 'User does not exist.')
        self.assertTrue(response.content_type == 'application/json')
        self.assertEqual(response.status_code, 404)

  def test_refresh_token(self):
    """ Test for user refresh token to issue new access token """
    with self.client:
        # user registration
        resp_register = register_user(self, 'yuanti', 'yuanti@gmail.com', 'freewifi')
        data_register = json.loads(resp_register.data.decode())
        self.assertTrue(data_register['status'] == 'success')
        self.assertTrue(data_register['access_token'])
        self.assertTrue(data_register['refresh_token'])
        self.assertTrue(resp_register.content_type == 'application/json')
        self.assertEqual(resp_register.status_code, 201)

        #attempt to refresh token
        response =  self.client.post(
        '/auth/refresh',
        headers=dict(
            Authorization='Bearer ' + json.loads(
                resp_register.data.decode()
            )['refresh_token']
        ),
        content_type='application/json',
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'success')
        self.assertTrue(data['access_token'] is not None)

  def test_user_status(self):
    """ Test to pull user status """
    with self.client:
        resp_register =  register_user(self, 'yuanti', 'yuanti@gmail.com', 'freewifi')
        response = self.client.get(
            '/auth/status',
            headers=dict(
                Authorization='Bearer ' + json.loads(
                    resp_register.data.decode()
                )['access_token']
            )
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'success')
        self.assertTrue(data['data'] is not None)
        self.assertTrue(data['data']['email'] == 'yuanti@gmail.com')
        self.assertTrue(data['data']['admin'] is 'true' or 'false')
        self.assertEqual(response.status_code, 200)

  def test_invalid_token_user_status(self):
    """ Test to pull user status with a refresh token"""
    with self.client:
        resp_register =  register_user(self, 'yuanti', 'yuanti@gmail.com', 'freewifi')
        response = self.client.get(
            '/auth/status',
            headers=dict(
                Authorization='Bearer ' + json.loads(
                    resp_register.data.decode()
                )['refresh_token']
            )
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'fail')
        self.assertTrue(data['message'] == 'Provide Valid access token.')
        self.assertEqual(response.status_code, 401)

  def test_valid_logout(self):
    """ Test for logout before token expires """
    with self.client:
        # user registration
        resp_register = register_user(self, 'yuanti', 'yuanti@gmail.com', 'freewifi')
        data_register = json.loads(resp_register.data.decode())
        self.assertTrue(data_register['status'] == 'success')
        self.assertTrue(data_register['refresh_token'])
        self.assertTrue(data_register['access_token'])
        self.assertTrue(resp_register.content_type == 'application/json')
        self.assertEqual(resp_register.status_code, 201)
        # user login
        resp_login = login_user(self, 'yuanti@gmail.com', 'freewifi')
        data_login = json.loads(resp_login.data.decode())
        self.assertTrue(data_login['status'] == 'success')
        self.assertTrue(data_login['message'] == 'Successfully logged in.')
        self.assertTrue(data_login['refresh_token'])
        self.assertTrue(data_login['access_token'])
        self.assertTrue(resp_login.content_type == 'application/json')
        self.assertEqual(resp_login.status_code, 200)
        # valid token logout
        response = self.client.post(
            '/auth/logout',
            headers=dict(
                Authorization='Bearer ' + json.loads(
                    resp_login.data.decode()
                )['refresh_token']
            )
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'success')
        self.assertTrue(data['message'] == 'Successfully logged out.')
        self.assertEqual(response.status_code, 200)

  def test_invalid_logout(self):
        """ Testing logout after the token expires """
        with self.client:
            # user registration
            resp_register = register_user(self,'joe_cool', 'joe@gmail.com', '123456')
            data_register = json.loads(resp_register.data.decode())
            self.assertTrue(data_register['status'] == 'success')
            self.assertTrue(data_register['refresh_token'])
            self.assertTrue(data_register['access_token'])
            self.assertTrue(resp_register.content_type == 'application/json')
            self.assertEqual(resp_register.status_code, 201)

            # user login
            resp_login = login_user(self, 'joe@gmail.com', '123456')
            data_login = json.loads(resp_login.data.decode())
            self.assertTrue(data_login['status'] == 'success')
            self.assertTrue(data_login['message'] == 'Successfully logged in.')
            self.assertTrue(data_login['refresh_token'])
            self.assertTrue(data_login['access_token'])
            self.assertTrue(resp_login.content_type == 'application/json')
            self.assertEqual(resp_login.status_code, 200)

            # invalid token logout
            time.sleep(6)
            response = self.client.post(
                '/auth/logout',
                headers=dict(
                    Authorization='Bearer ' + json.loads(
                        resp_login.data.decode()
                    )['refresh_token']
                )
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(
                data['message'] == 'Expired')
            self.assertEqual(response.status_code, 401)

  def test_valid_blacklisted_token_logout(self):
    """ Test for logout after a valid token gets blacklisted """
    with self.client:
        # user registration
        resp_register = self.client.post(
            '/auth/register',
            data=json.dumps(dict(
                email='joe@gmail.com',
                password='123456',
                username='joe_cool'
            )),
            content_type='application/json',
        )
        data_register = json.loads(resp_register.data.decode())
        self.assertTrue(data_register['status'] == 'success')
        self.assertTrue(
            data_register['message'] == 'Successfully registered.')
        self.assertTrue(data_register['refresh_token'])
        self.assertTrue(data_register['access_token'])
        self.assertTrue(resp_register.content_type == 'application/json')
        self.assertEqual(resp_register.status_code, 201)

      # user login
        resp_login = self.client.post(
            '/auth/login',
            data=json.dumps(dict(
                email='joe@gmail.com',
                password='123456'
            )),
            content_type='application/json'
        )
        data_login = json.loads(resp_login.data.decode())
        self.assertTrue(data_login['status'] == 'success')
        self.assertTrue(data_login['message'] == 'Successfully logged in.')
        self.assertTrue(data_login['refresh_token'])
        self.assertTrue(data_login['access_token'])
        self.assertTrue(resp_login.content_type == 'application/json')
        self.assertEqual(resp_login.status_code, 200)

        # blacklist a valid token
        blacklist_token = BlacklistToken(
            token=json.loads(resp_login.data.decode())['refresh_token'])
        db.session.add(blacklist_token)
        db.session.commit()
        # blacklisted valid token logout
        response = self.client.post(
            '/auth/logout',
            headers=dict(
                Authorization='Bearer ' + json.loads(
                    resp_login.data.decode()
                )['refresh_token']
            )
        )
        data = json.loads(response.data.decode())
        self.assertTrue(data['status'] == 'fail')
        self.assertTrue(data['message'] == 'Blacklisted')
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
     unittest.main()
