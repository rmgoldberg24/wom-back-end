from fastapi import Request, FastAPI, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pymongo import MongoClient
import motor.motor_asyncio
from bson.json_util import dumps
import json 
from mangum import Mangum

import os
from dotenv import load_dotenv
load_dotenv(override=True)

API_KEY = os.environ['PERPLEXITY_API_KEY']

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_DB_CONNECTION_STRING'])

mongoDB = client['wom']
# mongoCollection = mongoDB['recipes']
mongoCollection = mongoDB['recs']


origins = [
    "https://womrecs.app/",
    "https://womrecs.app",
    "https://www.womrecs.app/",
    "https://www.womrecs.app",
    "http://localhost:3000",
    "http://localhost:3000/",
    "https://f568-2603-8000-3af0-610-d9e5-71a2-3335-8969.ngrok-free.app",
    "https://f568-2603-8000-3af0-610-d9e5-71a2-3335-8969.ngrok-free.app/",
    "https://f1f9-76-33-147-6.ngrok-free.app/",
    "https://f1f9-76-33-147-6.ngrok-free.app",
]

app = FastAPI()

handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extractData(json_dict):
    print(json_dict)
    url = json_dict['url']
    message = 'Please identify the type and requested attributes located at {0}'.format(url)
    messages = [
    {
        "role": "system",
        "content": (
            "If the url is for a recipe, please provide a JSON with type equal to recipe, the recipe name (key = recipeName), ingredients, and steps."
            "If the url is for a restaurant, please provide a JSON with type equal to restaurant, the restaurant's name (key = name), address, phone number (key = phoneNumber), and type of food (key = foodType)."
            "If the url is for a hotel, please provide a JSON with type equal to hotel, the hotel's name (key = name), address, phone number (key = phoneNumber), and rating."
            "If the url is for a product, please provide a JSON with type equal to product, the product's name (key = name) , the product type (key = productType), and cost."
            "If the url is not for a recipe, restaurant, hotel, or product, please respond ONLY by saying EMPTY"
            "Please only return the final JSON. Do not return any additional text."
        ),
    },
    {
        "role": "user",
        "content": (
            message
        ),
    },
    ]
    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

    response = client.chat.completions.create(
        model="mistral-7b-instruct",
        messages=messages,
    )
    content = dict(dict(dict(response)['choices'][0])['message'])['content']

    if content != 'EMPTY':
        if content.count('{') > 1:
            formatted_content = '{' + content.split('{\n')[-1]
        else:
            formatted_content = '{' + content.split('{')[-1]
        response_json = json.loads(formatted_content)
    else:
        print('No can do!')
        return dumps({'type': 'invalid', 'message': "No supported content available at the provided URL. Please try a URL that contains information on a recipe, a restaurant, a hotel, or a product."})

    final_json = response_json | json_dict
    print(final_json)

    # Insert the document into the MongoDB collection
    result = mongoCollection.insert_one(final_json)
    return dumps(final_json)

@app.get('/')
async def hello():
    return {'hello' : 'welcome to the API'}

@app.post('/extract_data')
async def extract_data(request: Request):
    request_json = await request.body()
    json_dict = json.loads(request_json.decode('utf-8'))
    extracted_data = extractData(json_dict)
    return extracted_data

# @app.get('/view_recipes')
# async def view_recipes():
#     cursor = mongoCollection.find({})
#     recipes = await cursor.to_list(length=None)
#     print(type(dumps(recipes)))
#     print(dumps(recipes))
#     return dumps(recipes)

# @app.post('/view_my_recipes')
# async def view_my_recipes(request: Request):
#     request_json = await request.body()
#     user_id = request_json.decode('utf-8')
#     print(user_id)
#     cursor = mongoCollection.find({'user_id': user_id})
#     recipes = await cursor.to_list(length=None)
#     print(dumps(recipes))
#     return dumps(recipes)

@app.post('/view_my_data')
async def view_my_recipes(request: Request):
    request_json = await request.body()
    json_dict = json.loads(request_json.decode('utf-8'))
    print(json_dict)
    cursor = mongoCollection.find({
        'user_id': json_dict['user_id'], 
        'type': json_dict['type']
        })
    recs = await cursor.to_list(length=None)
    recs_json = dumps(recs)
    print(recs_json)
    return recs_json

@app.post('/slack_api')
async def slack_api(request: Request):
    request_json = await request.body()
    print(request_json)
    json_dict = json.loads(request_json.decode('utf-8'))
    print(json_dict)
    challenge = json_dict['challenge']
    print(challenge)
    return challenge

@app.post("/echo")
async def echo(request: Request, response: Response, data=Body(...)):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")

    print(data)

    return {
        "data": data,
        "raw_body": body,
        "headers": request.headers
    }

@app.post('/slack_api')
async def slack_api(request: Request):
    request_json = await request.body()
    print(request_json)
    return {'hi':'slack'}