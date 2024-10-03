vars_description = {
    "a_milk_tea": {
        "type": "ABrandTea",
        "is_global": True,
        "value": {
            "product": "MilkTea",
            "toppings": [
                {"_type": "Boba", "quantity": 10},
                {"_type": "TaroPaste", "quantity": 5}
            ],
            "size": "L"
        },
        "source": "data/vars/implementation.py",
    },
    "a_fruit_tea": {
        "type": "ABrandTea",
        "is_global": True,
        "value": {
            "product": "FruitTea",
            "toppings": [
                {"_type": "Pudding", "quantity": 3}
            ],
            "size": "M"
        },
        "source": "data/vars/implementation.py"
    },
    "b_milk_tea": {
        "type": "BBrandTea",
        "is_global": True,
        "value": {
            "product": "MilkTea",
            "toppings": [
                {"_type": "Boba", "quantity": 15},
                {"_type": "CoconutJelly", "quantity": 10}
            ],
            "size": "S"
        },
        "source": "data/vars/implementation.py"
    },
    "b_fruit_tea": {
        "type": "BBrandTea",
        "is_global": True,
        "value": {
            "product": "PureTea",
            "toppings": [
                {"_type": "Pudding", "quantity": 20}
            ],
            "size": "L"
        },
        "source": "data/vars/implementation.py"
    },
    "_user_account1": {
        "type": "UserInfo",
        "is_global": True,
        "value": {
            "id": 10000001,
            "password": "abc123.",
            "language": "en",
            "position": {
                "longitude_and_latitude": "42.6511674, -73.754968",
                "region": "US"
            },
            "key_and_host": {
                "key": "a6",
                "news_host": "go",
                "game_host": "epic-storm",
                "weather_host": "weathidapi.com",
                "movie_host": "moviei.com",
                "finance_host": "real-t.com",
                "sport_host": "spo.com"
            }
        },
        "source": "data/vars/implementation.py"
    },
    "_user_account2": {
        "type": "UserInfo",
        "is_global": True,
        "value": {
            "id": 10000002,
            "password": "ABC123.",
            "language": "en",
            "position": {
                "region": "JP"
            },
            "key_and_host": {
                "key": "af1423ea9db6",
                "news_host": "googi.com",
                "game_host": "epic-om",
                "weather_host": "com",
                "movie_host": "mov",
                "finance_host": "real-timrapi.com",
                "sport_host": "sporta.com"
            }
        },
        "source": "data/vars/implementation.py"
    },
    "_user_account3": {
        "type": "str",
        "is_global": True,
        "value": "test",
        "source": "data/vars/implementation.py"
    },
    "apis_statement": {
        "type": "str",
        "is_global": True,
        "value": """These APIs provide various data retrieval and processing functionalities:
1. **get_movie_data**: Fetches detailed information about movies from a specified online movie database, such as "Inception," using the user's API keys and host details to construct the request.
2. **get_weather_data**: Retrieves current weather conditions based on the longitude and latitude provided by the user, with the request including the user's API key and host information.
3. **get_google_news**: Obtains the latest news in the business category from Google News, tailored to the user's language and regional settings, with the API call including parameters for language-region and authentication headers.
4. **get_game_data**: Searches for upcoming game releases from the Epic Store based on user-provided search criteria and settings, filtering results by search words, categories, and user locale settings.
5. **get_finance_data**: Fetches real-time financial data for specified stock symbols, focusing on Apple Inc. stock with a period setting of '1D' (one day), authenticated using user-provided API keys.
6. **get_sport_data**: Provides data on sports events, specifically fetching head-to-head event details for a given event ID using the sport API, with the API call authenticated with user-specific headers.
7. **transform_json_news**: Transforms and reports JSON data from news APIs, formatted according to the system's current time and structured as an interaction between an AI butler and its master, dynamically adapting to include the latest system time in its response.
8. **deal_google_json**: Processes JSON data from a Google news API. If the response status is not 'success', it returns a failure message. Otherwise, it extracts and formats up to 8 news items, including the title, snippet, publisher, and related link, then returns them as a formatted string.
""",
        "source": "data/vars/implementation.py"
    },
    "user_account3": {
        "type": "UserInfo",
        "is_global": True,
        "value": {
            "id": 10000003,
            "password": "xyz789!",
            "position": {
                "longitude_and_latitude": "39.9042,116.4074",
                "detailed_address": "168 Wangfujing Street, Dongcheng District, Beijing, 100006, China",
                "region": "CN"
            },
            "key_and_host": {
                "key": "bca14234aaemsheabcd",
                "news_host": "china-.com",
                "game_host": "tencenapi.com",
                "weather_host": "chi.rapidapi.com",
                "movie_host": "chinese-c.com",
                "finance_host": "shanapidapi.com",
                "sport_host": "api.com",
            }
        },
        "source": "data/vars/implementation.py"
    },
    "_reader_profile": {
        "type": "ReaderProfile",
        "is_global": True,
        "value": {
            "id": 20000001,
            "name": "Emily",
            "preferred_genres": ["Science Fiction", "Fantasy"]
        },
        "source": "data/vars/reader_profile.py"
    },
    "_listener_profile": {
        "type": "ListenerProfile",
        "is_global": True,
        "value": {
            "id": 20000002,
            "name": "David",
            "favorite_artists": ["The Beatles", "Queen"]
        },
        "source": "data/vars/listener_profile.py"
    },
    "_patient_info": {
        "type": "PatientInfo",
        "is_global": True,
        "value": {
            "id": 20000003,
            "name": "Sarah",
            "medical_conditions": ["Hypertension"]
        },
        "source": "data/vars/patient_info.py"
    },
    "_student_profile": {
        "type": "StudentProfile",
        "is_global": True,
        "value": {
            "id": 20000004,
            "name": "John",
            "grade_level": "10th Grade",
            "subjects": ["Math", "Science"]
        },
        "source": "data/vars/student_profile.py"
    },
    "_client_profile": {
        "type": "ClientProfile",
        "is_global": True,
        "value": {
            "id": 20000005,
            "name": "Laura",
            "investment_goals": ["Retirement", "Education Fund"]
        },
        "source": "data/vars/client_profile.py"
    },
    "_user_account_fitness": {
        "type": "FitnessUserInfo",
        "is_global": True,
        "value": {
            "id": 10000004,
            "password": "Fitness123.",
            "language": "en",
            "position": {
                "longitude_and_latitude": "34.052235, -118.243683",
                "region": "US"
            },
            "key_and_host": {
                "key": "4a1e23dd4a2b340b834ab123",
                "fitness_host": "fitness-api.com",
                "diet_host": "diet-.com"
            }
        },
        "source": "data/vars/fitness_implementation.py"
    },
    "_date": {
        "type": "str",
        "is_global": True,
        "value": "2022-09-01",
        "source": "data/vars/fitness_implementation.py"
    },
    "_user_account_fitness_2": {
        "type": "FitnessUserInfo",
        "is_global": True,
        "value": {
            "id": 10000004,
            "password": "Fitness123.",
            "language": "en",
            "position": {
                "longitude_and_latitude": "34.052235, -118.243683",
                "region": "JP"
            },
            "key_and_host": {
                "key": "4a1e23dd4a2b1234ab123",
                "fitness_host": "fitness-appidapi.com",
                "diet_host": "diet-api.ppi.com"
            }
        },
        "source": "data/vars/fitness_implementation.py"
    },
}

