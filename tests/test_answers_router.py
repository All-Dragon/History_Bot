import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def created_question(client):
    response_create = await client.post('/users/create',
                                        json={'telegram_id': 101, 'username': 'IVAN', 'role': 'Преподаватель',
                                              'is_banned': False})
    token_response = await client.post('/auth/login', json={'telegram_id': response_create.json().get('telegram_id', 101)})
    token = token_response.json()['access_token']

    actual_user_id = response_create.json()['id']

    response = await client.post('/question/new',
                                 json={'text': 'Тестовый вопрос',
                                       'options': None,
                                       'correct_answer': 'correct_answer',
                                       'topic': 'topic',
                                       'difficulty': 5,
                                       'created_by': actual_user_id,
                                       'image_url': None,
                                       'status': 'published',
                                       'question_type': 'free_text'},
                                 headers={'Authorization': f"Bearer {token}"})
    return response.json(), token
async def test_create_answer(client, created_question):
    question, token = created_question
    response = await client.post('/answers/create',
                                 json = {'question_id': question.get('id'),
                                         'answer': question.get('correct_answer'),
                                         'is_correct': True},
                                 headers={'Authorization': f"Bearer {token}"} )
    assert response.status_code == 201
