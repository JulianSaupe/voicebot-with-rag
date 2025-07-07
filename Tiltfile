# Load Docker Compose for the database
docker_compose('./docker-compose.yaml')

dc_resource('postgres', labels=["Backend"])

# Define the backend service
local_resource(
    'API',
    serve_cmd='python -m backend.run_api',
    resource_deps=['postgres'],  # Ensure database is running before frontend
    labels=['Backend']
)

# Define the frontend service with hot reload
local_resource(
    'frontend',
    serve_cmd='cd frontend && npm run dev',
    deps=['frontend/src'],
    resource_deps=['postgres'],  # Ensure database is running before frontend
    labels=['Frontend'],
    links=[
        link('http://localhost:5173', 'Frontend App')
    ]
)

# Display helpful information
print("""
Voicebot Development Environment

Services:
- PostgreSQL Database: localhost:5050
- Frontend: http://localhost:5173

Commands:
- tilt up: Start all services
- tilt down: Stop all services
- tilt trigger prisma-migrate: Run Prisma migrations
- tilt trigger prisma-reset: Reset the database (caution: deletes all data)
""")
