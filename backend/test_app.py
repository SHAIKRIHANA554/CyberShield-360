"""Verification test script for CyberShield 360 backend & routing."""
import os
import sys
import unittest

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app


class TestCyberShield360(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'healthy')

    def test_page_routes(self):
        # Test clean URL routing
        for page in ['/', '/url-scanner', '/dashboard', '/pages/login.html', '/email-scanner', '/sms-scanner']:
            res = self.client.get(page)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'<html', res.data.lower())

    def test_guest_url_scan(self):
        res = self.client.post('/api/scanner/url', json={'url': 'http://hdfc-bank-kyc-update.ml/urgent/otp'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('data', {}).get('threat_level'), 'danger')

    def test_guest_sms_scan(self):
        res = self.client.post('/api/scanner/sms', json={'message': 'Urgent: Share your OTP immediately to unblock bank account'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('data', {}).get('threat_level'), 'danger')

    def test_guest_email_scan(self):
        res = self.client.post('/api/scanner/email', json={'content': 'Your SBI account is SUSPENDED due to missing KYC. Click http://sbi-kyc.ml', 'sender': 'support@gmail.com'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('data', {}).get('threat_level'), 'danger')

    def test_profile_after_registration_works_in_memory_fallback(self):
        register = self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'profile@test.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(register.status_code, 201)
        token = register.get_json()['data']['access_token']

        profile = self.client.get('/api/auth/profile', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(profile.status_code, 200)
        data = profile.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('data', {}).get('email'), 'profile@test.com')

    def test_seed_database_does_not_create_demo_user(self):
        from models.user_model import UserModel
        from seed_data import seed_database

        UserModel._col().delete_one({"email": "demo@cybershield360.com"})
        seed_database()

        self.assertIsNone(UserModel.find_by_email("demo@cybershield360.com"))

    def test_guest_pdf_download_works_after_scan(self):
        res = self.client.post('/api/scanner/url', json={'url': 'https://www.example.com'})
        self.assertEqual(res.status_code, 200)
        report_id = res.get_json()['data']['report_id']
        self.assertIsNotNone(report_id)

        pdf = self.client.get(f'/api/reports/{report_id}/pdf')
        self.assertEqual(pdf.status_code, 200)
        self.assertIn(b'%PDF', pdf.data[:8])

    def test_admin_can_publish_news_visible_to_users(self):
        admin_login = self.client.post('/api/auth/admin/login', json={
            'email': 'admin@cybershield360.com',
            'password': 'Admin@123'
        })
        self.assertEqual(admin_login.status_code, 200)
        token = admin_login.get_json()['data']['access_token']

        create_news = self.client.post('/api/admin/news', json={
            'title': 'Fake SMS scam network targeting Indian users',
            'summary': 'Authorities warn about a new scam pattern using phishing SMS messages.',
            'content': 'Attackers are sending fake bank alerts and urgent verification messages. Verify through official channels before acting.',
            'category': 'Cybercrime',
            'author': 'Security Operations',
            'tags': ['cybercrime', 'sms scam']
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(create_news.status_code, 201)

        feed = self.client.get('/api/news')
        self.assertEqual(feed.status_code, 200)
        self.assertIn('Fake SMS scam network targeting Indian users', feed.get_data(as_text=True))

    def test_quiz_can_be_loaded_and_submitted(self):
        register = self.client.post('/api/auth/register', json={
            'name': 'Quiz Test User',
            'email': 'quiz-flow@test.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(register.status_code, 201)
        token = register.get_json()['data']['access_token']

        quiz_list = self.client.get('/api/quiz')
        self.assertEqual(quiz_list.status_code, 200)
        quiz_id = quiz_list.get_json()['data']['items'][0]['_id']
        quiz_detail = self.client.get(f'/api/quiz/{quiz_id}')
        self.assertEqual(quiz_detail.status_code, 200)
        questions = quiz_detail.get_json()['data']['questions']
        self.assertNotIn('correct', questions[0])

        from models.quiz_model import QuizModel
        quiz_with_answers = QuizModel.find_by_id(quiz_id)
        answers = [question['correct'] for question in quiz_with_answers['questions']]
        submitted = self.client.post(
            f'/api/quiz/{quiz_id}/submit',
            json={'answers': answers, 'time_taken': 30},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.get_json()['data']['percentage'], 100)

    def test_learning_module_progress_can_be_saved(self):
        register = self.client.post('/api/auth/register', json={
            'name': 'Learning Test User',
            'email': 'learning-flow@test.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(register.status_code, 201)
        token = register.get_json()['data']['access_token']

        modules = self.client.get('/api/learning').get_json()['data']['items']
        module = next(item for item in modules if item.get('type') != 'cyber_law')
        headers = {'Authorization': f'Bearer {token}'}
        update = self.client.post(
            f"/api/learning/{module['_id']}/progress",
            json={'progress': 100},
            headers=headers
        )
        self.assertEqual(update.status_code, 200)

        progress = self.client.get('/api/learning/progress', headers=headers)
        self.assertEqual(progress.status_code, 200)
        self.assertTrue(any(item['module_id'] == module['_id'] and item['progress'] == 100
                            for item in progress.get_json()['data']))

    def test_admin_dashboard_shows_user_activity_and_manages_education(self):
        register = self.client.post('/api/auth/register', json={
            'name': 'Progress Test User',
            'email': 'admin-progress@test.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(register.status_code, 201)
        user_token = register.get_json()['data']['access_token']
        user_headers = {'Authorization': f'Bearer {user_token}'}

        login = self.client.post('/api/auth/login', json={
            'email': 'admin-progress@test.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(login.status_code, 200)
        user_token = login.get_json()['data']['access_token']
        user_headers = {'Authorization': f'Bearer {user_token}'}

        learning = self.client.get('/api/learning').get_json()['data']['items']
        module = next(item for item in learning if item.get('type') != 'cyber_law')
        progress = self.client.post(
            f"/api/learning/{module['_id']}/progress",
            json={'progress': 100}, headers=user_headers
        )
        self.assertEqual(progress.status_code, 200)

        quiz = self.client.get('/api/quiz').get_json()['data']['items'][0]
        self.assertNotIn('correct', quiz['questions'][0])
        quiz_submit = self.client.post(
            f"/api/quiz/{quiz['_id']}/submit",
            json={'answers': [0] * len(quiz['questions']), 'time_taken': 45},
            headers=user_headers
        )
        self.assertEqual(quiz_submit.status_code, 200)

        admin_login = self.client.post('/api/auth/admin/login', json={
            'email': 'admin@cybershield360.com',
            'password': 'Admin@123'
        })
        admin_token = admin_login.get_json()['data']['access_token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        dashboard = self.client.get('/api/admin/dashboard', headers=admin_headers)
        self.assertEqual(dashboard.status_code, 200)
        stats = dashboard.get_json()['data']
        self.assertEqual(stats['users_count'], 1)
        self.assertEqual(stats['logged_in_users_24h'], 1)
        self.assertEqual(stats['learning_progress']['completed_modules'], 1)
        self.assertEqual(stats['quiz_attempts_count'], 1)

        users = self.client.get('/api/admin/users', headers=admin_headers).get_json()['data']
        self.assertEqual(users['total'], 1)
        self.assertEqual(users['items'][0]['learning_completed'], 1)
        self.assertEqual(users['items'][0]['quiz_attempts'], 1)

        for endpoint in ['/api/admin/news', '/api/admin/learning?type=article',
                         '/api/admin/learning?type=cyber_law', '/api/admin/quiz']:
            self.assertEqual(self.client.get(endpoint, headers=admin_headers).status_code, 200)
        self.assertEqual(self.client.get('/api/admin/news', headers=user_headers).status_code, 403)

        admin_quizzes = self.client.get('/api/admin/quiz', headers=admin_headers).get_json()['data']['items']
        self.assertIn('correct', admin_quizzes[0]['questions'][0])


if __name__ == '__main__':
    unittest.main()
