import pytest
import pytest_asyncio


attribute = 'telegram_id, username, role, is_banned, text, options, correct_answer, topic, difficulty, image_url, status, question_type'
attribute_data = [
    (10, 'Ala', 'Преподаватель', False, 'Тестовый вопрос 1', None, 'тест', 'abi', 1, None, 'draft', 'free_text'),
    (11, 'Eve', 'Преподаватель', False, 'Тестовый вопрос 2', ['тестовый', 'test'], 'test', 'aaa', 1, None, 'published', 'multiple_choice')
]

@pytest_asyncio.fixture
async def created_question(client):
    response_create = await client.post('/users/create',
                                        json={'telegram_id': 100, 'username': 'IGOR', 'role': 'Преподаватель',
                                              'is_banned': False})
    token_response = await client.post('/auth/login', json={'telegram_id': response_create.json().get('telegram_id', 100)})
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
    return response.json()

@pytest.mark.parametrize(attribute, attribute_data)
async def test_create_answer(telegram_id, username, role, is_banned,text, options, correct_answer, topic,
                             difficulty, image_url, status,
                             question_type, client):

    response_create = await client.post('/users/create',
                                        json={'telegram_id': telegram_id, 'username': username, 'role': role,
                                              'is_banned': is_banned})
    token_response = await client.post('/auth/login', json={'telegram_id': telegram_id})
    token = token_response.json()['access_token']

    actual_user_id = response_create.json()['id']

    response = await client.post('/question/new',
                           json = {'text': text,
                                   'options': options,
                                   'correct_answer': correct_answer,
                                   'topic': topic,
                                   'difficulty': difficulty,
                                   'created_by': actual_user_id,
                                   'image_url': image_url,
                                   'status': status,
                                   'question_type': question_type},
                                 headers={'Authorization': f"Bearer {token}"})

    assert response.status_code == 201
    data = response.json()
    assert data.get('text') == text
    assert data.get('options') == options
    assert data.get('correct_answer') == correct_answer
    assert data.get('topic') == topic
    assert data.get('difficulty') == difficulty
    assert data.get('created_by') == actual_user_id
    assert data.get('image_url') == image_url
    assert data.get('status') == status
    assert data.get('question_type') == question_type

async def test_get_random_questions(client, created_question):
    response = await client.get('/question/random')
    print(response.json())
    assert response.status_code == 200

async def test_negative_get_random_questions(client):
    response = await client.get('/question/random')
    print(response.json())
    assert response.status_code == 404
    assert response.json().get('detail') == 'Нет опубликованных вопросов'

async def test_get_question_by_id(client, created_question):
    question_id = created_question.get('id', 1)
    response = await client.get(f'/question/{question_id}')
    assert response.status_code == 200