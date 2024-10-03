apis_description = {
    "calculate_a_brand_price": {
        "description": "Calculates the total price for A brand tea based on the type of tea, its size, the toppings included, and the quantity ordered. Each type of tea has a different base price, different cup sizes have different price multipliers, and each topping has a specific unit price.",
        "paras": {
            "tea": "ABrandTea",
            "quantity": "int"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "calculate_b_brand_price": {
        "description": "Calculates the total price for B brand tea. Similar to the A brand, but with different toppings and size price multipliers. The calculation is based on the tea's type, size, toppings, and quantity ordered. Each type of tea has a different base price, different cup sizes have varying price multipliers, and each topping has a specific unit price.",
        "paras": {
            "tea": "BBrandTea",
            "quantity": "int"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "presales_questions_and_answers": {
        "description": "...",
        "paras": {
            "question": "str"
        },
        "return": "str",
        "source": "data/apis/implementation.py"
    },
    "get_movie_data": {
        "description": "Fetches detailed information about movies from a specified online movie database. It constructs a request using the user's API keys and host details, querying the database for data on the movie 'Inception'.",
        "paras": {
            "user": "UserInfo"
        },
        "return": "dict",
        "source": "data/apis/implementation.py"
    },
    "get_weather_data": {
        "description": "Retrieves current weather conditions based on the longitude and latitude provided by the user. The request includes headers with the user’s API key and host information for the weather service.",
        "paras": {
            "user": "UserInfo"
        },
        "return": "dict",
        "source": "data/apis/implementation.py"
    },
    "get_google_news": {
        "description": "Obtains the latest news in the business category from Google News, tailored to the user's language and regional settings. The API call includes parameters for language-region and authentication headers.",
        "paras": {
            "user": "UserInfo",
        },
        "return": "dict",
        "source": "data/apis/implementation2.py"
    },
    "get_game_data": {
        "description": "Searches for upcoming game releases from the Epic Store based on user-provided search criteria and settings. It filters the results by search words, categories, and user locale settings.",
        "paras": {
            "user": "UserInfo",
            "search_words": "str"
        },
        "return": "dict",
        "source": "data/apis/implementation2.py",
    },
    "get_finance_data": {
        "description": "Fetches real-time financial data for specified stock symbols, focusing on the Apple Inc. stock with a period setting of '1D' (one day). The request is authenticated using user-provided API keys.",
        "paras": {
            "user": "UserInfo"
        },
        "return": "dict",
        "source": "data/apis/implementation2.py"
    },
    "get_sport_data": {
        "description": "Provides data on sports events, specifically fetching head-to-head event details for a given event ID using the sport API. The API call is authenticated with user-specific headers.",
        "paras": {
            "user": "UserInfo"
        },
        "return": "dict",
        "source": "data/apis/implementation.py",
    },
    "transform_json_news": {
        "description": "Transforms and reports JSON data from news APIs, formatted according to the system's current time and structured as an interaction between an AI butler and its master. It dynamically adapts to include the latest system time in its response.",
        "paras": {
            "json_data": "dict"
        },
        "return": "str",
        "source": "data/apis/implementation.py"
    },
    "deal_google_json": {
        "description": "Processes JSON data from a Google news API. If the response status is not 'success', it returns a failure message. Otherwise, it extracts and formats up to 8 news items, including the title, snippet, publisher, and related link, then returns them as a formatted string.",
        "paras": {
            "json_data": "dict"
        },
        "return": "str",
        "source": "data/apis/implementation.py"
    },
    "display_json_data": {
        "description": "It is used to intelligently convert JSON format information into content that can be directly broadcasted and displayed",
        "paras": {
            "json_data": "dict"
        },
        "source": "data/apis/implementation.py"
    },
    "extract_weather_condition": {
        "description": "Parses the weather data to extract the current weather condition (e.g., 'Sunny', 'Rainy'). Returns the weather condition as a string matching the WeatherCondition type.",
        "paras": {
            "weather_data": "dict"
        },
        "return": "WeatherCondition",
        "source": "data/apis/implementation.py"
    },
    "log_transport_suggestion": {
        "description": "Logs the transport suggestion made to the user for auditing and improvement purposes. Stores the user's ID and the suggested transport mode.",
        "paras": {
            "user": "UserInfo",
            "mode": "TransportMode"
        },
        "source": "data/apis/implementation.py"
    },
    "log_transport_information": {
        "description": "Logs the transport suggestion made to the user for auditing and improvement purposes. Stores the user's ID and the suggested transport mode.",
        "paras": {
            "user": "UserInfo",
            "mode": "TransportMode"
        },
        "return": "dict",
        "source": "data/apis/implementation.py"
    },
    "get_travel_data": {
        "description": "Retrieves current weather conditions based on the longitude and latitude provided by the user. The request includes headers with the user’s API key and host information for the weather service.",
        "paras": {
            "user": "UserInfo",
            "date": "str",
        },
        "return": "dict",
        "source": "data/apis/implementation.py"
    },
    "extract_current_price": {
        "description": "Extracts the current price from the provided price information dictionary.",
        "paras": {
            "price_info": "dict"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "extract_previous_price": {
        "description": "Extracts the previous closing price from the provided price information dictionary.",
        "paras": {
            "price_info": "dict"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "calculate_price_change": {
        "description": "Calculates the absolute difference between the current price and the previous closing price.",
        "paras": {
            "current_price": "float",
            "previous_price": "float"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "log_price_check": {
        "description": "Logs the price check performed for auditing and tracking purposes. Stores the user's ID and the price change detected.",
        "paras": {
            "user": "UserInfo",
            "change": "float"
        },
        "source": "data/apis/implementation.py"
    },
    "extract_temperature": {
        "description": "Extracts the current temperature from the weather data JSON object. Returns the temperature as a float in degrees Celsius.",
        "paras": {
            "weather_data": "dict"
        },
        "return": "float",
        "source": "data/apis/implementation.py"
    },
    "log_outfit_recommendation": {
        "description": "Logs the outfit recommendation provided to the user for future reference and analytics.",
        "paras": {
            "user": "UserInfo",
            "suggestion": "str"
        },
        "source": "data/apis/implementation.py"
    },
    "recommend_movie": {
        "description": "Filters the provided movie data based on the specified genre and returns a suitable movie suggestion as a string.",
        "paras": {
            "movies": "dict",
            "genre": "str"
        },
        "return": "str",
        "source": "data/apis/implementation.py"
    },
    "log_movie_suggestion": {
        "description": "Logs the movie suggestion provided to the user for future recommendations and analytics.",
        "paras": {
            "user": "UserInfo",
            "movie": "str"
        },
        "source": "data/apis/implementation.py"
    },
    "get_workout_plan": {
        "description": "Fetches a workout plan based on the user's selected workout type, using the user's API keys and preferences.",
        "paras": {
            "user": "FitnessUserInfo",
            "type": "WorkoutType"
        },
        "return": "WorkoutPlan",
        "source": "data/apis/fitness_implementation.py"
    },
    "get_diet_plan": {
        "description": "Fetches a diet plan tailored to the user's dietary preferences, using the user's API keys and preferences.",
        "paras": {
            "user": "FitnessUserInfo",
            "preference": "str"
        },
        "return": "DietPlan",
        "source": "data/apis/fitness_implementation.py"
    },
    "submit_user_progress": {
        "description": "Records the user's workout progress and updates their fitness profile with the completed plan. It returns a status message indicating whether the update was successful.",
        "paras": {
            "user": "FitnessUserInfo",
            "plan": "dict"
        },
        "return": "str",
        "source": "data/apis/fitness_implementation.py"
    },
    "log_daily_activity": {
        "description": "Logs the user's daily workout activity for tracking purposes. It does not return any value.",
        "paras": {
            "user": "FitnessUserInfo",
            "plan": "dict"
        },
        "source": "data/apis/fitness_implementation.py"
    }
}


