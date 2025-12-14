# PharmAI
AI-powered pharmacist assistant for a retail pharmacy chain.


# To build the image run the following command

docker build -t PharmAI .

# To run the container run the following command

docker run -p 8080:8080 PharmAI


detatched:
docker run -p 8080:8080 -d PharmAI




# Dev environment
Use volume to persist data

docker run --name pharmai-container -p 8080:8080 -v "$(pwd)/app":/app --env-file .env pharmai

# To do before submitting
- Remove dev environment binding (app folder copy)


# Libraries and technologies
- Langchain
- pydantic